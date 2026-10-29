#!/usr/bin/env python3
"""
llm_model_probe.py -- standalone: find out which LLM the Anthropic API exposes / actually serves.

Needs:  pip install anthropic   (optional: pyyaml, python-dotenv)
Auth:   export ANTHROPIC_API_KEY=...   (or a .env file in the cwd)

Usage
  python3 llm_model_probe.py list                       # models your key can use
  python3 llm_model_probe.py check claude-sonnet-4-6    # does this model id exist?
  python3 llm_model_probe.py probe claude-sonnet-4-6    # 1 tiny call: requested vs SERVED model
  python3 llm_model_probe.py audit                      # compare repro.yaml / env / code defaults, then probe
  add --json for machine-readable output, --out file.json to save it

Exit code 0 = OK, 1 = problem (unknown model, served != requested, drift between sources).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_client():
    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("anthropic SDK missing: pip install anthropic")
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ANTHROPIC_API_KEY is not set")
    return Anthropic(api_key=key)


# ───────────────────────── operations ─────────────────────────
def list_models(client) -> list[dict]:
    """GET /v1/models -- every model id this key can call."""
    return [{"id": m.id, "display_name": getattr(m, "display_name", None),
             "created_at": str(getattr(m, "created_at", ""))} for m in client.models.list()]


def check_model(client, model: str) -> dict:
    """GET /v1/models/{id} -- cheap existence check, no tokens spent."""
    try:
        m = client.models.retrieve(model)
        return {"model": model, "exists": True, "id": m.id,
                "display_name": getattr(m, "display_name", None)}
    except Exception as e:  # noqa: BLE001
        return {"model": model, "exists": False, "error": f"{type(e).__name__}: {e}"}


def probe_model(client, model: str) -> dict:
    """One minimal live call; reports requested vs served model, ids and usage."""
    t0 = time.perf_counter()
    try:
        raw = client.messages.with_raw_response.create(
            model=model, max_tokens=16,
            messages=[{"role": "user", "content": "Reply with the single word: ok"}])
        resp = raw.parse()
        request_id = raw.headers.get("request-id")
    except Exception as e:  # noqa: BLE001
        return {"model_requested": model, "ok": False, "error": f"{type(e).__name__}: {e}"}
    dt = time.perf_counter() - t0
    served = getattr(resp, "model", None)
    usage = getattr(resp, "usage", None)
    return {
        "model_requested": model,
        "model_served": served,
        # an alias (claude-sonnet-4-6) legitimately resolves to a dated snapshot id
        # (claude-sonnet-4-6-2026xxxx); only a different model family/version is a mismatch.
        "match": bool(served) and (served == model or served.startswith(model + "-")),
        "alias_resolved_to_snapshot": bool(served) and served != model and served.startswith(model + "-"),
        "response_id": getattr(resp, "id", None),
        "request_id": request_id,
        "stop_reason": getattr(resp, "stop_reason", None),
        "usage": {"in": getattr(usage, "input_tokens", None), "out": getattr(usage, "output_tokens", None)},
        "latency_s": round(dt, 3),
        "ok": True,
    }


# ───────────────────────── audit: where is the model id defined? ─────────────────────────
MODEL_RE = re.compile(r"claude-[a-z0-9]+(?:-[a-z0-9]+)*-\d[\w.-]*|claude-[a-z]+-\d(?:-\d+)?")


def find_sources(root: Path) -> dict:
    """Collect every model id the repo declares: env, repro.yaml, and string literals in .py files."""
    out: dict = {"env:HYPATIAX_LLM_MODEL": os.environ.get("HYPATIAX_LLM_MODEL") or None}
    cfg = Path(os.environ.get("REPRO_CFG") or root / "config" / "repro.yaml")
    out["repro.yaml:llm_model"] = None
    if cfg.is_file():
        try:
            import yaml
            out["repro.yaml:llm_model"] = (yaml.safe_load(cfg.read_text()) or {}).get("llm_model")
        except Exception:  # noqa: BLE001
            m = re.search(r"^llm_model:\s*[\"']?([^\"'\s#]+)", cfg.read_text(), re.M)
            out["repro.yaml:llm_model"] = m.group(1) if m else None
    literals: dict[str, list[str]] = {}
    skip = {".git", "__pycache__", ".venv", "venv", "node_modules"}
    for p in root.rglob("*.py"):
        if set(p.parts) & skip or p.resolve() == Path(__file__).resolve():
            continue
        try:
            for i, ln in enumerate(p.read_text(errors="replace").splitlines(), 1):
                if ln.lstrip().startswith("#"):
                    continue
                for m in MODEL_RE.findall(ln):
                    literals.setdefault(m, []).append(f"{p.relative_to(root)}:{i}")
        except OSError:
            pass
    out["code_literals"] = literals
    return out


def audit(client, root: Path) -> dict:
    src = find_sources(root)
    declared = {k: v for k, v in src.items() if k != "code_literals" and v}
    declared.update({f"code:{m}": m for m in src["code_literals"]})
    distinct = sorted({v for v in declared.values()})
    # model that would really be used: env > repro.yaml > (first code literal)
    effective = src["env:HYPATIAX_LLM_MODEL"] or src["repro.yaml:llm_model"] or (distinct[0] if distinct else None)
    res = {"sources": src, "distinct_model_ids": distinct, "drift": len(distinct) > 1, "effective": effective}
    res["all_ids_check"] = {m: check_model(client, m)["exists"] for m in distinct}
    res["nonexistent_ids"] = sorted(m for m, ok in res["all_ids_check"].items() if not ok)
    if effective:
        res["check"] = check_model(client, effective)
        res["probe"] = probe_model(client, effective) if res["check"]["exists"] else None
    return res


# ───────────────────────── CLI ─────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    for n in ("check", "probe"):
        sub.add_parser(n).add_argument("model")
    a_p = sub.add_parser("audit")
    a_p.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    client = get_client()
    if args.cmd == "list":
        res, bad = list_models(client), False
    elif args.cmd == "check":
        res = check_model(client, args.model); bad = not res["exists"]
    elif args.cmd == "probe":
        res = probe_model(client, args.model); bad = not res["ok"] or not res.get("match", False)
    else:
        res = audit(client, Path(args.root).resolve())
        bad = res["drift"] or bool(res["nonexistent_ids"]) or not (res.get("check") or {}).get("exists", False) \
            or not (res.get("probe") or {}).get("match", False)

    text = json.dumps(res, indent=2, default=str)
    if args.out:
        Path(args.out).write_text(text + "\n")
    if args.json or args.cmd == "audit":
        print(text)
    elif args.cmd == "list":
        for m in res:
            print(f"{m['id']:40} {m['display_name'] or ''}")
    else:
        for k, v in res.items():
            print(f"{k:16} {v}")
    if args.cmd == "audit":
        print("\nDRIFT: more than one model id is declared" if res["drift"] else "\nno drift between declared model ids",
              file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
