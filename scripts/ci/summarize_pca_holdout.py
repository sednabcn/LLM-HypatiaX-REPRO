#!/usr/bin/env python3
"""Build the Exp2 PCA summary from held-out PCA scores, never training R²."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

TARGET_METHODS = (
    "EnhancedHybridSystemDeFi (core)",
    "HybridDiscoverySystem v50_2 (tools)",
)
EXCLUDED_METHODS = {
    "HybridSystemLLMNN all-domains (core)": (
        "Historical result is marked unverified_no_formula and excluded "
        "from reported symbolic-recovery results."
    )
}
FORCED_LLM_DOMAINS = {
    "feynman_mechanics", "feynman_electromagnetism", "feynman_quantum",
    "feynman_thermodynamics", "feynman_optics",
}
NN_HYBRID_KEY = "HybridSystemLLMNN all-domains (core)"


def _finite_score(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        score = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return score if math.isfinite(score) else None


def build_summary(pca_dir: Path, threshold: float = 0.999999,
                  expected_equations: int = 30) -> dict:
    files = sorted(pca_dir.glob("protocol_core_noiseless_pca_*.json"))
    if not files:
        raise FileNotFoundError(
            f"No protocol_core_noiseless_pca_*.json files found in {pca_dir}"
        )

    cases = {}
    source_files = []
    decision_by_domain = {}

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        tests = data.get("tests") if isinstance(data, dict) else None
        if not isinstance(tests, list):
            raise ValueError(f"{path.name}: expected a top-level tests array")
        source_files.append(path.name)

        for test in tests:
            if not isinstance(test, dict):
                raise ValueError(f"{path.name}: malformed test record")
            description = str(test.get("description") or "").strip()
            if not description:
                raise ValueError(f"{path.name}: test record has no description")
            if description in cases:
                raise ValueError(
                    f"Duplicate PCA equation record {description!r} in "
                    f"{cases[description]} and {path.name}; refusing to inflate denominator"
                )
            cases[description] = path.name

            results = test.get("results") or {}
            pca_scores = test.get("pca_test_r2") or {}
            if not isinstance(results, dict) or not isinstance(pca_scores, dict):
                raise ValueError(f"{path.name}: malformed results/pca_test_r2 mapping")

            nn_result = results.get(NN_HYBRID_KEY) or {}
            nn_meta = nn_result.get("metadata") or {}
            decision = nn_meta.get("decision")
            domain = test.get("domain")
            if decision is not None and domain is not None:
                entry = decision_by_domain.setdefault(
                    domain, {"llm": 0, "other": 0, "forced": domain in FORCED_LLM_DOMAINS}
                )
                if decision == "llm":
                    entry["llm"] += 1
                else:
                    entry["other"] += 1

            cases[description] = {
                "file": path.name,
                "results": results,
                "pca_scores": pca_scores,
            }

    per_method = {}
    for method in TARGET_METHODS:
        n_pass = n_available = n_failed = n_excluded = 0
        failure_reasons = {}
        scores = []
        for description, case in cases.items():
            result = case["results"].get(method)
            if result is None:
                n_failed += 1
                failure_reasons["missing_method_record"] = (
                    failure_reasons.get("missing_method_record", 0) + 1
                )
                continue
            metadata = result.get("metadata") or {}
            if (
                result.get("exclude_from_reported_results")
                or metadata.get("exclude_from_reported_results")
                or metadata.get("provenance_status") in {
                    "unverified_no_formula", "contaminated"
                }
            ):
                n_excluded += 1
                continue

            score = _finite_score(case["pca_scores"].get(method))
            if not result.get("success") or score is None:
                n_failed += 1
                status = (
                    result.get("external_holdout_error")
                    or metadata.get("external_holdout_error")
                    or "PCA holdout score unavailable or method failed"
                )
                failure_reasons[status] = failure_reasons.get(status, 0) + 1
                continue

            n_available += 1
            scores.append(score)
            if score >= threshold:
                n_pass += 1

        n_total = len(cases) - n_excluded
        per_method[method] = {
            "n_pass": n_pass,
            "n_total": n_total,
            "n_available": n_available,
            "n_failed_or_unavailable": n_failed,
            "n_excluded": n_excluded,
            "solve_rate": n_pass / n_total if n_total else None,
            "mean_pca_test_r2": sum(scores) / len(scores) if scores else None,
            "failure_reasons": failure_reasons,
        }

    n_pass_total = sum(v["n_pass"] for v in per_method.values())
    n_total_total = sum(v["n_total"] for v in per_method.values())
    forced_llm = sum(v["llm"] for v in decision_by_domain.values() if v["forced"])
    forced_total = sum(v["llm"] + v["other"] for v in decision_by_domain.values() if v["forced"])
    natural_llm = sum(v["llm"] for v in decision_by_domain.values() if not v["forced"])
    natural_total = sum(v["llm"] + v["other"] for v in decision_by_domain.values() if not v["forced"])

    return {
        "fixc3_step": "exp2_feynman_pca_4060",
        "description": "PCA holdout recovery summary; held-out 60% only",
        "split_protocol": "pca_40_60",
        "train_fraction": 0.4,
        "test_fraction": 0.6,
        "extrap_train_frac": 0.4,
        "extrap_multiplier": 2.0,
        "scoring_field": "tests[].pca_test_r2[method]",
        "threshold": threshold,
        "expected_equations": expected_equations,
        "observed_equations": len(cases),
        "protocol_complete": (
            len(cases) == expected_equations
            and all(
                v["n_total"] == expected_equations
                and v["failure_reasons"].get("missing_method_record", 0) == 0
                for v in per_method.values()
            )
        ),
        "n_pass": n_pass_total,
        "n_total": n_total_total,
        "solve_rate": n_pass_total / n_total_total if n_total_total else None,
        "per_method": per_method,
        "excluded_methods": EXCLUDED_METHODS,
        "hybrid_llm_routing": {
            "forced_domains": sorted(FORCED_LLM_DOMAINS),
            "forced_llm_count": f"{forced_llm}/{forced_total}" if forced_total else "0/0",
            "natural_llm_count": f"{natural_llm}/{natural_total}" if natural_total else "0/0",
            "by_domain": {
                domain: {
                    "llm": value["llm"],
                    "other": value["other"],
                    "forced": value["forced"],
                }
                for domain, value in sorted(decision_by_domain.items())
            },
        },
        "source_files": source_files,
        "interpretation": (
            "Training R² is not used for the PCA solve rate. Missing or non-finite "
            "holdout scores count as failures. The unverified all-domains method "
            "is excluded from the reported method comparison."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pca-dir", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--threshold", type=float, default=0.999999)
    parser.add_argument("--expected-equations", type=int, default=30)
    args = parser.parse_args()
    summary = build_summary(args.pca_dir, args.threshold, args.expected_equations)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n",
                            encoding="utf-8")
    print(
        f"[PCA-HOLDOUT] {summary['n_pass']}/{summary['n_total']} "
        f"({summary['solve_rate']:.1%}) at R² >= {args.threshold}"
    )
    for method, result in summary["per_method"].items():
        print(
            f"[PCA-HOLDOUT] {method}: {result['n_pass']}/{result['n_total']} "
            f"available={result['n_available']} failed/unavailable="
            f"{result['n_failed_or_unavailable']}"
        )
    if not summary["protocol_complete"]:
        print(
            f"[PCA-HOLDOUT] WARNING: expected {args.expected_equations} equations, "
            f"found {summary['observed_equations']}"
        )


if __name__ == "__main__":
    main()
