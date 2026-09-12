#!/usr/bin/env python3
"""
Item-1 Pure-LLM API diagnostic shard.

Runs exactly 3 DeFi catalogue cases and ONLY the PureLLM generation path.
The purpose is to prove whether every case reaches Anthropic's
client.messages.create() or whether later cases are short-circuited.

Expected output markers from the patched baseline:
    GENERATE_ENTER
    API_ENTER
    API_EXIT        or API_ERROR

Run from the LLM-HypatiaX-REPRO repository root:

    export PYTHONUNBUFFERED=1
    python hypatiax/experiments/benchmarks/diagnostic_item1_3cases.py \
        2>&1 | tee item1_3case.log

Optional:
    ITEM1_N_CASES=2 ...    # run 2 instead of 3
    ITEM1_CASES="Value at Risk at 95%,Value at Risk at 99%" ...
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

# Repository root = .../LLM-HypatiaX-REPRO
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol
from hypatiax.core.base_pure_llm.baseline_pure_llm_defi_discovery import (
    PureLLMBaseline,
)
from hypatiax.experiments.benchmarks.hypatiax_defi_benchmark_v4 import (
    _get_test_cases,
)


MODEL = os.environ.get("ITEM1_MODEL", "claude-sonnet-4-6")
N_CASES = int(os.environ.get("ITEM1_N_CASES", "3"))
CASE_FILTER = os.environ.get("ITEM1_CASES", "").strip()

OUT = Path(os.environ.get("ITEM1_DIAG_OUT", "item1_3case_diagnostic.json"))


def _select_cases():
    catalogue = _get_test_cases()

    if CASE_FILTER:
        wanted = [x.strip().lower() for x in CASE_FILTER.split(",") if x.strip()]
        selected = [
            tc for tc in catalogue
            if any(w in tc["name"].lower() for w in wanted)
        ]
    else:
        selected = catalogue[:N_CASES]

    if not selected:
        raise RuntimeError("No diagnostic cases selected.")

    return selected[:N_CASES]


def _serialise(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if not np.isfinite(obj) else float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(type(obj).__name__)


def main():
    cases = _select_cases()
    protocol = DeFiExperimentProtocol()
    results = []

    print("=" * 88)
    print("ITEM 1 — PURE LLM API DIAGNOSTIC SHARD")
    print("=" * 88)
    print(f"repo_root={ROOT}")
    print(f"model={MODEL!r}")
    print(f"cases={len(cases)}")
    print(f"baseline_source={inspect.getsourcefile(PureLLMBaseline)!r}")
    print(f"generate_formula_source={inspect.getsourcefile(PureLLMBaseline.generate_formula)!r}")
    print("=" * 88)

    for idx, tc in enumerate(cases, 1):
        name = tc["name"]
        print(f"\n[{idx}/{len(cases)}] {name}")

        t_case = time.perf_counter()
        rec = {
            "index": idx,
            "case": name,
            "domain": tc["domain"],
            "model_requested": MODEL,
        }

        try:
            protocol_cases = protocol.load_test_data(
                tc["domain"], num_samples=tc["num_samples"]
            )
            match = next(
                (
                    (d, X, y, v, m)
                    for d, X, y, v, m in protocol_cases
                    if name.lower() in d.lower()
                ),
                None,
            )
            if match is None:
                raise RuntimeError(f"No protocol match for {name!r}")

            desc, X, y, var_names, metadata = match
            metadata = dict(metadata or {})
            metadata.update({
                "extrapolation_test": True,
                "difficulty": tc["difficulty"],
                "formula_type": tc["formula_type"],
            })

            rec.update({
                "description_hash": hashlib.sha256(desc.encode()).hexdigest()[:12],
                "description": desc,
                "variable_names": var_names,
            })

            # Deliberately create a NEW baseline for each case, exactly like v4.
            llm = PureLLMBaseline(model=MODEL)

            rec["baseline_id"] = id(llm)
            rec["client_id"] = id(llm.client)
            rec["client_type"] = (
                f"{type(llm.client).__module__}.{type(llm.client).__name__}"
            )
            rec["cache_attribute_present"] = hasattr(llm, "_cache")
            rec["cache_value"] = repr(getattr(llm, "_cache", None))

            print(
                "CASE_SETUP "
                f"baseline_id={id(llm)} "
                f"client_id={id(llm.client)} "
                f"cache_attribute_present={hasattr(llm, '_cache')} "
                f"cache={getattr(llm, '_cache', None)!r}"
            )

            # IMPORTANT: no X/y scoring here. generate_formula() alone is the
            # object of the diagnostic. Hardcoded formulas may return without
            # an API call; that is visible because API_ENTER will be absent.
            result = llm.generate_formula(
                desc, tc["domain"], var_names, metadata
            )

            rec["elapsed_s"] = round(time.perf_counter() - t_case, 6)
            rec["result_method"] = result.get("method")
            rec["result_model"] = result.get("model")
            rec["has_python_code"] = bool(
                result.get("python_code") or result.get("formula_code")
            )
            rec["raw_response_hash"] = hashlib.sha256(
                (result.get("raw_response") or "").encode()
            ).hexdigest()[:12]
            rec["error_type"] = result.get("error_type")
            rec["error"] = result.get("error")
            rec["error_repr"] = result.get("error_repr")

            print(
                "CASE_RESULT "
                f"elapsed={rec['elapsed_s']:.6f}s "
                f"method={rec['result_method']!r} "
                f"model={rec['result_model']!r} "
                f"has_python_code={rec['has_python_code']} "
                f"error_type={rec['error_type']!r}"
            )

        except Exception as e:
            rec["elapsed_s"] = round(time.perf_counter() - t_case, 6)
            rec["outer_error_type"] = type(e).__name__
            rec["outer_error"] = str(e)
            rec["outer_error_repr"] = repr(e)
            print(
                "CASE_OUTER_ERROR "
                f"elapsed={rec['elapsed_s']:.6f}s "
                f"type={type(e).__name__} "
                f"message={str(e)!r}"
            )

        results.append(rec)

    OUT.write_text(
        json.dumps(results, indent=2, default=_serialise)
    )

    print("\n" + "=" * 88)
    print(f"Saved: {OUT}")
    print("=" * 88)
    print("\nINTERPRETATION:")
    print("  API_ENTER + API_EXIT for every case  -> all cases reached Anthropic.")
    print("  API_ENTER only for case 1            -> later cases are short-circuited before API.")
    print("  API_ENTER + API_ERROR                 -> real API failure; inspect exception.")
    print("  No API_ENTER on a case                -> generate_formula returned before API.")
    print("=" * 88)


if __name__ == "__main__":
    main()
