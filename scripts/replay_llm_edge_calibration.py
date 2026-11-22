#!/usr/bin/env python3
"""Replay saved LLM formulas on their original DeFi core/edge rows, without LLM calls.

The replay regenerates protocol arrays in canonical catalogue order and refuses
to score any row unless the original split indices and SHA-256 hashes match.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hypatiax.core.routing import training_edge_split_indices
from hypatiax.experiments.benchmarks import hypatiax_defi_benchmark_v3c as benchmark
from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol
from scripts.calibrate_llm_edge_degradation import (
    _array_hash, _evaluate_formula_pair, _match_protocol_case, _summarize,
)


def replay(input_path: Path, output_path: Path) -> dict:
    saved = json.loads(input_path.read_text(encoding="utf-8"))
    source_records = {r["equation_id"]: r for r in saved.get("records", [])}
    cases = benchmark._get_test_cases()
    if len(cases) != 74 or len(source_records) != 74:
        raise RuntimeError(
            f"Expected canonical 74 cases/records; got {len(cases)}/{len(source_records)}"
        )

    protocol = DeFiExperimentProtocol()
    replayed = []
    # Preserve the exact original case iteration order: some protocol
    # generators use NumPy's process-global RNG.
    for case in cases:
        name = case["name"]
        record = source_records.get(name)
        if record is None:
            raise RuntimeError(f"Missing saved calibration record: {name}")
        result = {
            "equation_id": name,
            "cohort": record.get("cohort"),
            "original_status": record.get("status"),
            "formula_present": bool(record.get("formula")),
            "replay_status": "not_replayed",
        }
        formula = record.get("formula")

        matches = protocol.load_test_data(case["domain"], num_samples=case["num_samples"])
        match = _match_protocol_case(name, matches)
        if match is None:
            raise RuntimeError(f"Protocol case no longer resolves: {name}")
        _, X_full, y_full, _, metadata = match
        X_train, y_train, _, _, outer_split = benchmark._aggressive_split(
            X_full, y_full, case["config"], return_metadata=True
        )
        core_idx, edge_idx = training_edge_split_indices(X_train, 0.15)

        # A replay is only valid if the exact inputs match the generation run.
        checks = {
            "n_core": len(core_idx) == record.get("n_core"),
            "n_edge": len(edge_idx) == record.get("n_edge"),
            "core_indices": core_idx.astype(int).tolist()
                == record.get("core_indices_in_outer_train"),
            "edge_indices": edge_idx.astype(int).tolist()
                == record.get("edge_indices_in_outer_train"),
            "core_hash": _array_hash(X_train[core_idx], y_train[core_idx])
                == record.get("core_examples_sha256"),
            "edge_hash": _array_hash(X_train[edge_idx], y_train[edge_idx])
                == record.get("edge_data_sha256"),
            "outer_split": outer_split == record.get("outer_split"),
        }
        result["input_integrity_checks"] = checks
        if not all(checks.values()):
            result["replay_status"] = "integrity_mismatch"
            result["reason"] = "Regenerated protocol inputs differ from generation artifact"
            replayed.append(result)
            continue
        if not formula:
            result["replay_status"] = "no_saved_formula"
            result["reason"] = "Original generation did not return a formula"
            replayed.append(result)
            continue

        scored = _evaluate_formula_pair(
            formula, X_train[core_idx], y_train[core_idx],
            X_train[edge_idx], y_train[edge_idx],
            constants=(metadata or {}).get("constants") or {},
        )
        result["core_diagnostics"] = scored.get("core")
        result["edge_diagnostics"] = scored.get("edge")
        if scored.get("ok"):
            result.update({
                "replay_status": "scored",
                "r2_core": scored["core"]["r2"],
                "r2_edge": scored["edge"]["r2"],
                "delta_r2_core_minus_edge": scored["delta_llm"],
                "delta_nrmse_core_scale": scored["delta_nrmse_core_scale"],
            })
        else:
            result["replay_status"] = "score_undefined"
            result["reason"] = scored.get("failure_reason")
        replayed.append(result)

    # Summaries deliberately descriptive; no tau selection or threshold fitting.
    summary_records = [{
        "cohort": r.get("cohort"),
        "status": "scored" if r.get("replay_status") == "scored" else r.get("replay_status"),
        "delta_llm": r.get("delta_r2_core_minus_edge"),
        "delta_nrmse_core_scale": r.get("delta_nrmse_core_scale"),
        "core_diagnostics": r.get("core_diagnostics"),
        "edge_diagnostics": r.get("edge_diagnostics"),
    } for r in replayed if r.get("cohort") in {"calibration", "evaluation"}]
    summary = _summarize(summary_records)
    output = {
        "replay_protocol": "llm-edge-calibration-replay-v1",
        "source_protocol_version": saved.get("protocol_version"),
        "source_model": saved.get("model"),
        "source_split_seed": saved.get("split_seed"),
        "source_artifact": input_path.name,
        "n_records": len(replayed),
        "n_integrity_verified": sum(
            r.get("replay_status") in {"scored", "score_undefined", "no_saved_formula"}
            and all((r.get("input_integrity_checks") or {}).values())
            for r in replayed
        ),
        "n_integrity_mismatch": sum(r.get("replay_status") == "integrity_mismatch" for r in replayed),
        "summary": summary,
        "records": replayed,
        "tau_selected": None,
        "tau_eligibility": "not_eligible: no predeclared acceptable-fit criterion",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({
        "n_records": output["n_records"],
        "n_integrity_verified": output["n_integrity_verified"],
        "n_integrity_mismatch": output["n_integrity_mismatch"],
        "replay_status_counts": {
            status: sum(r.get("replay_status") == status for r in replayed)
            for status in sorted({r.get("replay_status") for r in replayed})
        },
        "summary": summary,
        "output": str(output_path),
        "tau_selected": None,
    }, indent=2))
    if output["n_integrity_mismatch"]:
        raise RuntimeError("Replay aborted: one or more original input hashes/indices did not match")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    replay(args.input, args.output)


if __name__ == "__main__":
    main()
