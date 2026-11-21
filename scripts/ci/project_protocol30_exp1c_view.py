#!/usr/bin/env python3
"""Create the exp1c two-method view from a validated Protocol-30 PCA aggregate.

This is a deterministic projection of an existing six-method aggregate. It
never executes a model, changes the source aggregate, or creates a new protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


METHOD_IDS = (2, 3)  # one-based runner registry IDs
METHOD_NAMES = ("ImprovedNN", "EnhancedHybridDeFi")


def project_protocol30_exp1c(source_path: Path, output_path: Path) -> dict[str, Any]:
    source_path = source_path.resolve()
    output_path = output_path.resolve()
    if source_path == output_path:
        raise ValueError("projection output must not overwrite the source aggregate")
    if not source_path.is_file():
        raise ValueError(f"source aggregate does not exist: {source_path}")

    raw = source_path.read_bytes()
    try:
        source = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"source aggregate is not valid strict JSON: {exc}") from exc

    if not isinstance(source, dict):
        raise ValueError("source aggregate must be a JSON object")
    aggregate = source.get("protocol30_aggregate")
    protocol = source.get("protocol")
    methods = source.get("methods")
    tests = source.get("tests")

    if not isinstance(aggregate, dict) or aggregate.get("variant") != "pca_4060":
        raise ValueError("source is not a validated Protocol-30 PCA 40/60 aggregate")
    if aggregate.get("equation_count") != 30 or aggregate.get("shard_count") != 5:
        raise ValueError("source aggregate does not certify five shards and 30 equations")
    if not isinstance(protocol, dict):
        raise ValueError("source aggregate is missing protocol metadata")
    if protocol.get("mode") != "noiseless_pca" or protocol.get("noise_injected") is not False:
        raise ValueError("source protocol is not the noiseless PCA variant")
    if float(protocol.get("noise_level", -1)) != 0.0 or protocol.get("n_samples") != 200:
        raise ValueError("source protocol sample/noise settings do not match Protocol-30 PCA")
    if source.get("total_tests") != 30 or not isinstance(tests, list) or len(tests) != 30:
        raise ValueError("source aggregate must contain exactly 30 test records")
    if not isinstance(methods, list) or len(methods) != 6 or len(set(methods)) != 6:
        raise ValueError("source aggregate must preserve all six distinct registered methods")
    if len(methods) < 3 or tuple(methods[1:3]) != METHOD_NAMES:
        raise ValueError(
            "Protocol-30 method registry IDs 2 and 3 are not the expected "
            f"{METHOD_NAMES!r}; found {methods!r}"
        )

    projected_tests = []
    for index, record in enumerate(tests, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"test record {index} is not an object")
        results = record.get("results")
        if not isinstance(results, dict) or set(results) != set(methods):
            raise ValueError(f"test record {index} does not preserve all six method results")
        projected = {key: value for key, value in record.items() if key != "results"}
        projected["results"] = {name: results[name] for name in METHOD_NAMES}
        projected_tests.append(projected)

    output = {
        "artifact_type": "derived_method_projection",
        "alias_id": "exp1c",
        "alias_of": "exp1",
        "protocol_variant": "protocol30_pca_40_60",
        "runner_stage": "exp2_protocol30_pca_4060",
        "method_ids": list(METHOD_IDS),
        "method_names": list(METHOD_NAMES),
        "source_artifact": source_path.name,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_protocol30_aggregate": aggregate,
        "source_methods": methods,
        "timestamp": source.get("timestamp"),
        "protocol": protocol,
        "total_tests": 30,
        "tests": projected_tests,
        "projection_only": True,
        "execution_performed": False,
        "note": (
            "Deterministic two-method projection of the validated six-method "
            "Protocol-30 PCA aggregate; this is not a new experiment or rerun."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = project_protocol30_exp1c(args.input, args.output)
    print(
        f"PASS: exp1c view contains {result['total_tests']} equations and "
        f"methods {result['method_ids']} -> {args.output}"
    )


if __name__ == "__main__":
    main()
