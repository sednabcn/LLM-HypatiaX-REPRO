# audit: ignore[F1] meta/resolver helper: writes a config file, not experiment result rows
"""Resolver + meta helper for scripts/run_pure_llm_arm.py.

Place in scripts/ (the runner puts scripts/ on sys.path when run as a script).

Usage:
  # 1. resolver: equation name -> the CORE_15 dict that generate_data() expects
  --equation-resolver exp1_resolver:resolve

  # 2. meta file: {name: {description, domain, variable_names, constants}}
  python scripts/exp1_resolver.py config/equations_meta.json
  --equations-meta config/equations_meta.json

Check the generated meta against the frozen prompts before trusting it:
  archive/phase2/phase2_finish_out/rendered_p_requests/<Equation_Name>.txt

[AUDIT-L2] The description goes into the LLM prompt. It must never fall back to the true
formula (the old chain was description -> desc -> formula -> name). For the current CORE_15 no
entry has description/desc/formula, so the description is the equation NAME ("Michaelis-Menten",
"Ideal Gas Law", ...). That is not a formula leak, but it IS a recall channel: a textbook name
lets the LLM answer from memory. build_meta() now warns about it instead of doing it silently.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from hypatiax.experiments.benchmarks.exp1_ablation import CORE_15  # noqa: E402

_BY_NAME = {eq["name"]: eq for eq in CORE_15}


def resolve(name):
    """Equation name -> CORE_15 dict (what generate_data needs)."""
    try:
        return _BY_NAME[name]
    except KeyError:
        raise KeyError(f"{name!r} not in CORE_15; known: {sorted(_BY_NAME)}")


def build_meta():
    meta, name_only = {}, []
    for eq in CORE_15:
        # NO formula fallback, ever: this text is sent to the LLM.
        desc = eq.get("description") or eq.get("desc")
        if not desc:
            desc = eq["name"]
            name_only.append(eq["name"])
        meta[eq["name"]] = {
            # VERIFY against rendered_p_requests/*.txt, the frozen prompt is the truth.
            "description": desc,
            "domain": eq["domain"],
            "variable_names": list(eq["vars"]),
            "constants": eq.get("constants", {}),
        }
    if name_only:
        print(f"[resolver] WARNING: {len(name_only)}/{len(CORE_15)} equations use their textbook NAME "
              "as the LLM description (recall channel, see module docstring): "
              + ", ".join(name_only), file=sys.stderr)
    return meta


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "config" / "equations_meta.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_meta(), indent=2, default=str), encoding="utf-8")
    print(f"wrote {out} ({len(CORE_15)} equations)")
