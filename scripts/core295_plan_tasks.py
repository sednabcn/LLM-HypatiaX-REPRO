#!/usr/bin/env python3
"""Build a deterministic Core-295 task manifest from a fully accepted catalogue.

This is a planning-only utility. It does not generate data, call models, launch
workers, modify the catalogue, or run experiments.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

DOMAINS = ("Chemistry", "Biology", "Physics", "DeFi AMM", "DeFi Risk")
SCHEMA = "core295-task-manifest-v1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def fail(message: str) -> None:
    raise SystemExit(f"BLOCKED: {message}")


def validate_catalogue(catalogue: object) -> list[dict]:
    if not isinstance(catalogue, dict):
        fail("catalogue root must be a JSON object")
    if catalogue.get("status") != "ready":
        fail(f"catalogue status must be 'ready', got {catalogue.get('status')!r}")
    if catalogue.get("target_equation_count") != 295:
        fail("target_equation_count must equal 295")
    if catalogue.get("per_domain_target") != 59:
        fail("per_domain_target must equal 59")
    frame = catalogue.get("sampling_frame")
    if not isinstance(frame, dict) or frame.get("status") != "frozen":
        fail("sampling_frame.status must be 'frozen'")
    for field in ("source_universe", "inclusion_exclusion_rules", "selection_method",
                  "independent_statistical_unit", "source_family_definition"):
        if not frame.get(field):
            fail(f"sampling_frame.{field} is required")

    entries = catalogue.get("entries")
    if not isinstance(entries, list) or len(entries) != 295:
        fail("catalogue must contain exactly 295 entry objects")
    source_rows = catalogue.get("source_register")
    if not isinstance(source_rows, list):
        fail("source_register must be an array")
    sources = {x.get("source_id"): x for x in source_rows
               if isinstance(x, dict) and isinstance(x.get("source_id"), str)}
    if len(sources) != len([x for x in source_rows if isinstance(x, dict) and x.get("source_id")]):
        fail("source_register contains duplicate source_id values")

    seen_ids, seen_fingerprints, seen_independence_units = set(), set(), set()
    counts = Counter()
    tasks = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            fail(f"entries[{index}] is not an object")
        eid = entry.get("equation_id")
        domain = entry.get("domain")
        if not isinstance(eid, str) or not eid.strip():
            fail(f"entries[{index}] has no equation_id")
        if eid in seen_ids:
            fail(f"duplicate equation_id: {eid}")
        seen_ids.add(eid)
        if domain not in DOMAINS:
            fail(f"{eid}: unsupported domain {domain!r}")
        counts[domain] += 1
        if entry.get("status") != "accepted":
            fail(f"{eid}: status is not accepted")
        fingerprint = entry.get("structural_fingerprint")
        if not isinstance(fingerprint, str) or not fingerprint.strip():
            fail(f"{eid}: structural_fingerprint is missing")
        if fingerprint in seen_fingerprints:
            fail(f"{eid}: duplicate structural_fingerprint")
        seen_fingerprints.add(fingerprint)
        if not entry.get("canonical_expression") or not entry.get("formula"):
            fail(f"{eid}: canonical_expression and formula are required")
        family_id = entry.get("source_family_id")
        unit_id = entry.get("independence_unit_id")
        if not isinstance(family_id, str) or not family_id.strip():
            fail(f"{eid}: source_family_id must be a non-empty string")
        if not isinstance(unit_id, str) or not unit_id.strip():
            fail(f"{eid}: independence_unit_id must be a non-empty string")
        if unit_id in seen_independence_units:
            fail(f"{eid}: duplicate independence_unit_id {unit_id!r}; statistical units must be unique")
        seen_independence_units.add(unit_id)
        if not entry.get("reviewer") or not entry.get("reviewed_on"):
            fail(f"{eid}: reviewer and reviewed_on are required")
        review = entry.get("equivalence_review")
        if not isinstance(review, dict) or review.get("classification") != "E4" or not review.get("rationale"):
            fail(f"{eid}: accepted entry requires documented E4 review and rationale")
        refs = entry.get("source_ids")
        if not isinstance(refs, list) or not refs:
            fail(f"{eid}: at least one registered source_id is required")
        if not any(ref in sources and sources[ref].get("domain") in (domain, "cross-domain") for ref in refs):
            fail(f"{eid}: no source-register record matches the entry domain")
        generator = entry.get("generator")
        if not isinstance(generator, dict) or generator.get("status") != "ready":
            fail(f"{eid}: generator.status must be ready before task planning")
        for field in ("model_class", "method", "seed_policy", "parameter_sampling",
                      "sampling_semantics", "parameter_sampling_scope"):
            if not generator.get(field):
                fail(f"{eid}: generator.{field} is required")
        allowed_model_classes = {
            "explicit_scalar", "implicit_scalar", "coupled_algebraic_system",
            "ode_ivp", "difference_system", "stochastic_process",
            "protocol_simulation", "matrix_operator",
        }
        model = entry.get("model_definition")
        if not isinstance(model, dict) or model.get("model_class") not in allowed_model_classes:
            fail(f"{eid}: model_definition.model_class must be a supported declared class")
        if generator.get("model_class") != model.get("model_class"):
            fail(f"{eid}: generator.model_class must match model_definition.model_class")
        role_fields = ("independent_variables", "dependent_variables", "state_variables",
                       "fixed_parameters", "physical_constants")
        roles = {}
        for role in role_fields:
            values = model.get(role)
            if not isinstance(values, list) or any(not isinstance(x, str) or not x for x in values):
                fail(f"{eid}: model_definition.{role} must be a list of symbol names")
                values = []
            for symbol in values:
                if symbol in roles:
                    fail(f"{eid}: symbol {symbol} is assigned to multiple variable roles")
                roles[symbol] = role
        variables = entry.get("variables")
        if not isinstance(variables, dict) or not variables:
            fail(f"{eid}: variables must be a non-empty object")
        if set(roles) != set(variables):
            fail(f"{eid}: variable-role declarations must partition exactly the variables dictionary")
        inputs = set(model.get("independent_variables", []))
        validity = entry.get("input_validity_bounds")
        if not isinstance(validity, dict) or set(validity) != inputs:
            fail(f"{eid}: input_validity_bounds must cover exactly independent inputs")
        for variable in inputs:
            bounds = validity[variable]
            if (not isinstance(bounds, list) or len(bounds) != 2
                    or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)) for v in bounds)
                    or float(bounds[0]) >= float(bounds[1])):
                fail(f"{eid}: invalid input_validity_bounds for {variable}")
        ranges = entry.get("input_ranges")
        if not isinstance(ranges, dict) or set(ranges) != inputs:
            fail(f"{eid}: input_ranges must cover exactly independent_variables (not parameters/constants/states)")
        for variable, bounds in ranges.items():
            if not isinstance(bounds, dict):
                fail(f"{eid}: range record for {variable} must be an object")
            for kind in ("train", "extrapolation"):
                interval = bounds.get(kind)
                if (not isinstance(interval, list) or len(interval) != 2
                        or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)) for v in interval)
                        or float(interval[0]) >= float(interval[1])):
                    fail(f"{eid}: invalid {kind} interval for {variable}")
            valid_lo, valid_hi = map(float, validity[variable])
            train_hi = float(bounds["train"][1])
            if train_hi <= 0:
                fail(f"{eid}: {variable} requires a positive training upper bound for Core-15 near/far extrapolation")
            generated = [*map(float, bounds["train"]), *map(float, bounds["extrapolation"]),
                         train_hi, train_hi * 1.5, train_hi * 4.0, train_hi * 6.0]
            if min(generated) < valid_lo or max(generated) > valid_hi:
                fail(f"{eid}: generated train/near/medium/far ranges exceed validity bounds for {variable}")
        if not isinstance(model.get("constraints"), list) or not model.get("operator_structure"):
            fail(f"{eid}: model constraints and operator_structure are required")
        if generator.get("constraints_enforced") is not True:
            fail(f"{eid}: generator.constraints_enforced must be true before planning")
        if not isinstance(generator.get("constraint_evidence"), str) or not generator["constraint_evidence"].strip():
            fail(f"{eid}: generator.constraint_evidence is required")
        if generator.get("constraint_enforcement_method") != "rectangular_input_bounds_v1":
            fail(f"{eid}: only rectangular_input_bounds_v1 is currently supported")
        for value_field, role in (("fixed_parameter_values", "fixed_parameters"),
                                  ("physical_constant_values", "physical_constants")):
            values = entry.get(value_field)
            if not isinstance(values, dict) or set(values) != set(model[role]):
                fail(f"{eid}: {value_field} must cover exactly model_definition.{role}")
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v))
                   for v in values.values()):
                fail(f"{eid}: {value_field} must contain only finite numeric values")
        tasks.append({"equation_id": eid, "domain": domain, "fingerprint": fingerprint,
                      "model_class": model["model_class"],
                      "source_family_id": entry["source_family_id"],
                      "independence_unit_id": entry["independence_unit_id"]})
    for domain in DOMAINS:
        if counts[domain] != 59:
            fail(f"{domain}: expected 59 accepted equations, found {counts[domain]}")
    if len({x["independence_unit_id"] for x in tasks}) != 295:
        fail("independence_unit_id values are not 295 unique statistical units")
    return sorted(tasks, key=lambda x: (DOMAINS.index(x["domain"]), x["equation_id"]))


def assign_shards(tasks: list[dict], shard_count: int) -> list[dict]:
    if shard_count < 1 or shard_count > 295:
        fail("shard count must be between 1 and 295")
    buckets = [[] for _ in range(shard_count)]
    # Round-robin within each domain. Each domain's task sequence is sorted by ID;
    # shard rotation continues across domains to balance total load deterministically.
    cursor = 0
    for domain in DOMAINS:
        domain_tasks = [t for t in tasks if t["domain"] == domain]
        for task in domain_tasks:
            buckets[cursor % shard_count].append(task["equation_id"])
            cursor += 1
    planned = []
    for shard_id, ids in enumerate(buckets):
        planned.append({"shard_id": shard_id, "equation_ids": ids,
                        "equation_count": len(ids)})
    flattened = [eid for shard in planned for eid in shard["equation_ids"]]
    if len(flattened) != len(set(flattened)) or set(flattened) != {t["equation_id"] for t in tasks}:
        fail("internal exact-once shard assignment check failed")
    return planned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=Path("config/core295_catalogue.json"))
    parser.add_argument("--shards", type=int, default=100)
    parser.add_argument("--output", type=Path, required=True,
                        help="new manifest path; existing files are never overwritten")
    parser.add_argument("--run-id", required=True,
                        help="caller-supplied immutable run label; not a GitHub Actions run")
    args = parser.parse_args()
    try:
        raw = args.catalogue.read_bytes()
        catalogue = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read catalogue: {exc}")
    tasks = validate_catalogue(catalogue)
    shards = assign_shards(tasks, args.shards)
    task_payload = {"tasks": tasks, "shards": shards}
    manifest = {
        "schema": SCHEMA,
        "run_id": args.run_id,
        "catalogue_path": str(args.catalogue),
        "catalogue_sha256": sha256_bytes(raw),
        "task_set_sha256": sha256_bytes(canonical_json(tasks)),
        "shard_plan_sha256": sha256_bytes(canonical_json(task_payload)),
        "target_equation_count": 295,
        "per_domain_target": 59,
        "shard_count": args.shards,
        "assignment": "deterministic round-robin, domain ordered, equation_id sorted",
        "tasks": tasks,
        "shards": shards,
        "planning_only": True,
        "experiments_executed": False,
        "acceptance_authority": "none"
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("xb") as stream:
            stream.write(canonical_json(manifest))
    except FileExistsError:
        fail(f"refusing to overwrite existing manifest: {args.output}")
    print(json.dumps({"status": "PLANNED", "equations": len(tasks),
                      "shards": len(shards), "manifest": str(args.output),
                      "catalogue_sha256": manifest["catalogue_sha256"],
                      "task_set_sha256": manifest["task_set_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
