"""Make LLM seed guesses fit PySR's active operator set *before* fit(), and record what happened.

    kept, dropped = sanitize_guesses(["-x0**2 + 0.16", "sign(x0)", "x0**0.75"],
                                     binary_ops=["+", "-", "*", "/"], unary_ops=["sqrt"],
                                     variables=["x0"])
    # kept    -> ['(0.16 - (x0 * x0))']
    # dropped -> [('sign(x0)', 'unsupported_operator:sign'), ('x0**0.75', 'needs_pow')]

Rules: ** or ^ needs "^" or "pow" in binary_ops (integer powers 2..4 are expanded to products);
unary minus becomes 0 - x; sign()/unknown functions/unknown names are dropped with a reason.
Nothing here is Julia-specific, so a bad guess is rejected up front instead of failing inside fit().

Audit: the engine calls record_audit(...) once per fit; the adapter calls drain_audit() to get the
row fields that phase3_close.py's G9 check requires.
"""
import ast
import hashlib
import math
import re

_ALIASES = {"ln": "log", "Abs": "abs", "arctan": "atan", "arcsin": "asin", "arccos": "acos"}
_CONSTS = {"pi": math.pi}


class _Drop(Exception):
    pass


def _unary_names(unary_ops):
    return {re.split(r"[(=\s]", u.strip(), maxsplit=1)[0] for u in (unary_ops or [])}


def sanitize_guesses(guesses, binary_ops, unary_ops, variables):
    binary = {b.strip() for b in (binary_ops or [])}
    unary = _unary_names(unary_ops)
    names = set(variables or [])
    kept, dropped, seen = [], [], set()

    def need(op):
        if op not in binary:
            raise _Drop(f"unsupported_operator:{op}")

    def pow_(a, b):
        if "^" in binary:
            return f"({a} ^ {b})"
        if "pow" in binary:
            return f"pow({a}, {b})"
        raise _Drop("needs_pow")

    def emit(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            if not math.isfinite(n.value):
                raise _Drop("nonfinite_constant")
            return repr(float(n.value)) if isinstance(n.value, float) else str(n.value)
        if isinstance(n, ast.Name):
            if n.id in names:
                return n.id
            if n.id in _CONSTS:
                return repr(_CONSTS[n.id])
            raise _Drop(f"unknown_name:{n.id}")
        if isinstance(n, ast.UnaryOp):
            if isinstance(n.op, ast.UAdd):
                return emit(n.operand)
            if isinstance(n.op, ast.USub):
                need("-")
                return f"(0 - {emit(n.operand)})"
            raise _Drop("unsupported_syntax:unary")
        if isinstance(n, ast.BinOp):
            op = type(n.op)
            if op is ast.Pow:
                e = n.right
                if isinstance(e, ast.Constant) and isinstance(e.value, (int, float)) and float(e.value).is_integer() \
                        and 2 <= int(e.value) <= 4:
                    need("*")
                    a = emit(n.left)
                    out = a
                    for _ in range(int(e.value) - 1):
                        out = f"({out} * {a})"
                    return out
                if isinstance(e, ast.Constant) and e.value == 1:
                    return emit(n.left)
                return pow_(emit(n.left), emit(e))
            sym = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}.get(op)
            if sym is None:
                raise _Drop(f"unsupported_operator:{op.__name__}")
            # fold unary minus into the neighbouring +/- so we emit a - b, not (0 - b) + a
            if sym == "+" and isinstance(n.left, ast.UnaryOp) and isinstance(n.left.op, ast.USub):
                need("-")
                return f"({emit(n.right)} - {emit(n.left.operand)})"
            if sym == "+" and isinstance(n.right, ast.UnaryOp) and isinstance(n.right.op, ast.USub):
                need("-")
                return f"({emit(n.left)} - {emit(n.right.operand)})"
            if sym == "-" and isinstance(n.right, ast.UnaryOp) and isinstance(n.right.op, ast.USub):
                need("+")
                return f"({emit(n.left)} + {emit(n.right.operand)})"
            need(sym)
            return f"({emit(n.left)} {sym} {emit(n.right)})"
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and not n.keywords:
            f = _ALIASES.get(n.func.id, n.func.id)
            if f == "pow" and len(n.args) == 2:
                return pow_(emit(n.args[0]), emit(n.args[1]))
            if f in unary and len(n.args) == 1:
                return f"{f}({emit(n.args[0])})"
            raise _Drop(f"unsupported_operator:{n.func.id}")
        raise _Drop(f"unsupported_syntax:{type(n).__name__}")

    for g in guesses or []:
        try:
            tree = ast.parse(str(g).replace("^", "**").strip(), mode="eval")
            out = emit(tree.body)
        except _Drop as d:
            dropped.append((g, str(d)))
            continue
        except (SyntaxError, ValueError, RecursionError):
            dropped.append((g, "unparseable"))
            continue
        if out in seen:
            dropped.append((g, "duplicate"))
            continue
        seen.add(out)
        kept.append(out)
    return kept, dropped


# ---------------------------------------------------------------- audit
_AUDIT = []


def reset_audit():
    _AUDIT.clear()


def record_audit(requested, kept, dropped, fit_fallback=False):
    """Log one fit's seed outcome. Returns the (mutable) record so the engine can attach it to its
    result dict and flag a later in-fit fallback with mark_fit_fallback()."""
    rec = {"requested": list(requested or []), "used": len(kept), "dropped": list(dropped),
           "fallback": bool(fit_fallback)}
    _AUDIT.append(rec)
    return rec


def mark_fit_fallback(rec):
    """The fit with guesses= failed and was retried without them: the seed did NOT take effect."""
    if rec is not None:
        rec["fallback"] = True


def summarize(records):
    req = [g for x in records for g in x["requested"]]
    return {
        "guesses_requested": sum(len(x["requested"]) for x in records),
        "guesses_used": sum(x["used"] for x in records),
        "guesses_dropped": sum(len(x["dropped"]) for x in records),
        "guess_dropped_reasons": sorted({r for x in records for _, r in x["dropped"]}),
        "guess_fit_fallback": any(x["fallback"] for x in records),
        "llm_sample_sha256": hashlib.sha256("\n".join(sorted(req)).encode()).hexdigest() if req else None,
    }


def drain_audit():
    """Row fields for the adapter (consumed by phase3_close.py G9). Clears the log."""
    out = summarize(list(_AUDIT))
    _AUDIT.clear()
    return out
