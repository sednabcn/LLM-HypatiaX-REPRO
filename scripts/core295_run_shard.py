#!/usr/bin/env python3
"""Fail-closed Core-295 shard driver with domain adapter boundary.

No experiment runs unless --execute is supplied. Domain adapters own the
scientific data generator and model invocation; this driver owns identity,
deterministic seed material, arm coverage, and artifact provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
from typing import Any

MANIFEST_SCHEMA = "core295-task-manifest-v1"
RESULT_SCHEMA = "core295-ablation-shard-v1"
DOMAINS = ("Chemistry", "Biology", "Physics", "DeFi AMM", "DeFi Risk")
ARMS = ("pysr_only", "hypatia", "hypatia_nollm")
STATUSES = {"success", "failed", "timeout", "skipped"}


def stop(message: str) -> None:
    raise SystemExit("BLOCKED: " + message)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
        return json.loads(raw), raw
    except (OSError, json.JSONDecodeError) as exc:
        stop(f"cannot read valid JSON at {path}: {exc}")


def validate_inputs(manifest: Any, manifest_raw: bytes, catalogue: Any,
                    catalogue_raw: bytes, shard_id: int) -> tuple[list[dict], dict]:
    if not isinstance(manifest, dict) or manifest.get("schema") != MANIFEST_SCHEMA:
        stop("task manifest schema mismatch")
    if manifest.get("planning_only") is not True or manifest.get("experiments_executed") is not False:
        stop("manifest must be the immutable planning-only task manifest")
    if manifest.get("catalogue_sha256") != sha(catalogue_raw):
        stop("catalogue bytes do not match manifest catalogue_sha256")
    if not isinstance(catalogue, dict) or catalogue.get("status") != "ready":
        stop("catalogue.status must be ready")
    if catalogue.get("target_equation_count") != 295 or catalogue.get("per_domain_target") != 59:
        stop("catalogue must declare the frozen 295/59 design")
    frame = catalogue.get("sampling_frame")
    if not isinstance(frame, dict) or frame.get("status") != "frozen":
        stop("sampling_frame.status must be frozen")
    for field in ("source_universe", "inclusion_exclusion_rules", "selection_method",
                  "independent_statistical_unit", "source_family_definition"):
        if not frame.get(field):
            stop(f"sampling_frame.{field} is required")
    entries = catalogue.get("entries")
    if not isinstance(entries, list) or len(entries) != 295:
        stop("catalogue must contain exactly 295 entries")
    by_id = {}
    counts = {domain: 0 for domain in DOMAINS}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("equation_id"), str):
            stop("catalogue contains malformed equation entry")
        eid = entry["equation_id"]
        if eid in by_id:
            stop(f"duplicate catalogue equation ID {eid}")
        if entry.get("status") != "accepted":
            stop(f"{eid}: entry is not accepted")
        review = entry.get("equivalence_review")
        if not isinstance(review, dict) or review.get("classification") != "E4" or not review.get("rationale"):
            stop(f"{eid}: documented E4 structural review is required")
        if not entry.get("source_family_id") or not entry.get("independence_unit_id"):
            stop(f"{eid}: source-family and statistical-unit IDs are required")
        if entry.get("domain") not in counts:
            stop(f"{eid}: unsupported domain")
        counts[entry["domain"]] += 1
        gen = entry.get("generator")
        if not isinstance(gen, dict) or gen.get("status") != "ready":
            stop(f"{eid}: generator.status is not ready")
        for field in ("model_class", "method", "seed_policy", "parameter_sampling",
                      "sampling_semantics", "parameter_sampling_scope"):
            if not isinstance(gen.get(field), str) or not gen[field].strip():
                stop(f"{eid}: generator.{field} is required")
        model = entry.get("model_definition")
        allowed_model_classes = {
            "explicit_scalar", "implicit_scalar", "coupled_algebraic_system",
            "ode_ivp", "difference_system", "stochastic_process",
            "protocol_simulation", "matrix_operator",
        }
        if not isinstance(model, dict) or model.get("model_class") not in allowed_model_classes:
            stop(f"{eid}: model_definition.model_class is missing or unsupported")
        if gen.get("model_class") != model.get("model_class"):
            stop(f"{eid}: generator.model_class must match model_definition.model_class")
        role_fields = ("independent_variables", "dependent_variables", "state_variables",
                       "fixed_parameters", "physical_constants")
        roles = {}
        for role in role_fields:
            values = model.get(role)
            if not isinstance(values, list) or any(not isinstance(x, str) or not x for x in values):
                stop(f"{eid}: model_definition.{role} must be a list of symbol names")
            for symbol in values:
                if symbol in roles:
                    stop(f"{eid}: symbol {symbol} is assigned to multiple variable roles")
                roles[symbol] = role
        variables = entry.get("variables")
        if not isinstance(variables, dict) or not variables or set(roles) != set(variables):
            stop(f"{eid}: variable-role declarations must partition the variables dictionary")
        validity = entry.get("input_validity_bounds")
        inputs = set(model["independent_variables"])
        if not isinstance(validity, dict) or set(validity) != inputs:
            stop(f"{eid}: input_validity_bounds must cover exactly independent inputs")
        for variable in inputs:
            bounds = validity[variable]
            if (not isinstance(bounds, list) or len(bounds) != 2
                    or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not __import__("math").isfinite(float(v)) for v in bounds)
                    or float(bounds[0]) >= float(bounds[1])):
                stop(f"{eid}: invalid input_validity_bounds for {variable}")
        ranges = entry.get("input_ranges")
        if not isinstance(ranges, dict) or set(ranges) != inputs:
            stop(f"{eid}: input_ranges must cover exactly independent_variables")
        for var, bounds in ranges.items():
            if not isinstance(bounds, dict):
                stop(f"{eid}: range record for {var} must be an object")
            for kind in ("train", "extrapolation"):
                interval = bounds.get(kind)
                if (not isinstance(interval, list) or len(interval) != 2
                        or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not __import__("math").isfinite(float(v)) for v in interval)
                        or float(interval[0]) >= float(interval[1])):
                    stop(f"{eid}: invalid {kind} interval for {var}")
            valid_lo, valid_hi = map(float, validity[var])
            train_hi = float(bounds["train"][1])
            if train_hi <= 0:
                stop(f"{eid}: {var} requires a positive training upper bound for Core-15 near/far extrapolation")
            generated = [*map(float, bounds["train"]), *map(float, bounds["extrapolation"]),
                         train_hi, train_hi * 1.5, train_hi * 4.0, train_hi * 6.0]
            if min(generated) < valid_lo or max(generated) > valid_hi:
                stop(f"{eid}: generated train/near/medium/far ranges exceed validity bounds for {var}")
        if not isinstance(model.get("constraints"), list) or not model.get("operator_structure"):
            stop(f"{eid}: model constraints and operator_structure are required")
        if gen.get("constraints_enforced") is not True:
            stop(f"{eid}: generator.constraints_enforced must be true before execution")
        if not isinstance(gen.get("constraint_evidence"), str) or not gen["constraint_evidence"].strip():
            stop(f"{eid}: generator.constraint_evidence is required")
        if gen.get("constraint_enforcement_method") != "rectangular_input_bounds_v1":
            stop(f"{eid}: only rectangular_input_bounds_v1 is currently supported")
        for value_field, role in (("fixed_parameter_values", "fixed_parameters"),
                                  ("physical_constant_values", "physical_constants")):
            values = entry.get(value_field)
            if not isinstance(values, dict) or set(values) != set(model[role]):
                stop(f"{eid}: {value_field} must cover exactly model_definition.{role}")
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not __import__("math").isfinite(float(v))
                   for v in values.values()):
                stop(f"{eid}: {value_field} must contain only finite numeric values")
        by_id[eid] = entry
    if any(counts[d] != 59 for d in DOMAINS):
        stop(f"domain counts must be exactly 59 each; found {counts}")

    tasks = manifest.get("tasks")
    shards = manifest.get("shards")
    if not isinstance(tasks, list) or not isinstance(shards, list):
        stop("manifest tasks and shards must be arrays")
    if sha(canonical(tasks)) != manifest.get("task_set_sha256"):
        stop("manifest task-set hash mismatch")
    if sha(canonical({"tasks": tasks, "shards": shards})) != manifest.get("shard_plan_sha256"):
        stop("manifest shard-plan hash mismatch")
    if len(tasks) != 295 or len({t.get("equation_id") for t in tasks if isinstance(t, dict)}) != 295:
        stop("manifest task list must contain 295 unique equation IDs")
    if any(t["equation_id"] not in by_id for t in tasks):
        stop("manifest includes an equation absent from the frozen catalogue")
    if {t["equation_id"] for t in tasks} != set(by_id):
        stop("manifest task IDs do not exactly match catalogue IDs")
    if type(manifest.get("shard_count")) is not int or manifest["shard_count"] < 1:
        stop("manifest shard_count must be a positive integer")
    if len(shards) != manifest["shard_count"]:
        stop("manifest shard_count does not match shard list")
    shard_ids = [s.get("shard_id") for s in shards if isinstance(s, dict)]
    if len(shard_ids) != len(shards) or len(set(shard_ids)) != len(shard_ids):
        stop("manifest shard rows are malformed or duplicated")
    if set(shard_ids) != set(range(manifest["shard_count"])):
        stop("manifest shard IDs must be contiguous from zero")
    flattened = []
    for shard in shards:
        ids_in_shard = shard.get("equation_ids")
        if not isinstance(ids_in_shard, list) or not all(isinstance(x, str) for x in ids_in_shard):
            stop("manifest contains malformed shard equation_ids")
        if shard.get("equation_count") != len(ids_in_shard):
            stop("manifest shard equation_count mismatch")
        flattened.extend(ids_in_shard)
    if len(flattened) != len(set(flattened)) or set(flattened) != {t.get("equation_id") for t in tasks if isinstance(t, dict)}:
        stop("manifest shard assignment is not exact-once")
    matches = [s for s in shards if isinstance(s, dict) and type(s.get("shard_id")) is int and s["shard_id"] == shard_id]
    if len(matches) != 1:
        stop(f"shard {shard_id} is not uniquely defined")
    ids = matches[0].get("equation_ids")
    if not isinstance(ids, list) or len(ids) != len(set(ids)):
        stop("shard equation IDs malformed or duplicated")
    task_map = {t["equation_id"]: t for t in tasks}
    if any(eid not in task_map for eid in ids):
        stop("shard references task outside manifest")
    selected = []
    for eid in ids:
        task = task_map[eid]
        entry = by_id[eid]
        if task.get("domain") != entry.get("domain") or task.get("fingerprint") != entry.get("structural_fingerprint"):
            stop(f"{eid}: manifest task metadata differs from catalogue")
        selected.append(entry)
    return selected, manifest


def load_adapter(spec: str):
    if ":" not in spec:
        stop("adapter must be module.path:callable")
    module_name, function_name = spec.split(":", 1)
    if not module_name or not function_name:
        stop("adapter must be module.path:callable")
    try:
        module = importlib.import_module(module_name)
        function = getattr(module, function_name)
    except (ImportError, AttributeError) as exc:
        stop(f"cannot load adapter {spec}: {exc}")
    if not callable(function):
        stop(f"adapter {spec} is not callable")
    return function


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--shard-id", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--adapter", action="append", default=[], metavar="DOMAIN=MODULE:CALLABLE",
                        help="one trusted adapter per domain represented in this shard")
    parser.add_argument("--execute", action="store_true",
                        help="explicitly invoke domain adapters; without this flag the driver refuses to run")
    parser.add_argument("--allow-live-services", action="store_true",
                        help="explicitly allow adapters to use live external model/API services")
    args = parser.parse_args()
    if not args.execute:
        stop("execution is opt-in; pass --execute only when authorized to run this shard")
    if not args.manifest.is_file() or not args.catalogue.is_file():
        stop("manifest and catalogue files must exist")
    manifest, manifest_raw = read_json(args.manifest)
    catalogue, catalogue_raw = read_json(args.catalogue)
    entries, m = validate_inputs(manifest, manifest_raw, catalogue, catalogue_raw, args.shard_id)

    adapters = {}
    for item in args.adapter:
        if "=" not in item:
            stop(f"invalid --adapter {item!r}; expected DOMAIN=MODULE:CALLABLE")
        domain, spec = item.split("=", 1)
        if domain not in DOMAINS or domain in adapters:
            stop(f"unsupported or duplicate adapter domain {domain!r}")
        adapters[domain] = load_adapter(spec)
    needed = {e["domain"] for e in entries}
    if needed != set(adapters):
        stop(f"provide exactly one adapter for each shard domain; needed={sorted(needed)}, supplied={sorted(adapters)}")

    results = []
    for entry in entries:
        eid, domain = entry["equation_id"], entry["domain"]
        seed_material = sha((m["run_id"] + "\0" + eid + "\0" + entry["generator"]["seed_policy"]).encode())
        context = {
            "run_id": m["run_id"],
            "shard_id": args.shard_id,
            "catalogue_sha256": m["catalogue_sha256"],
            "task_set_sha256": m["task_set_sha256"],
            "seed_material_sha256": seed_material,
            "required_arms": list(ARMS),
            "allow_live_services": args.allow_live_services,
        }
        try:
            returned = adapters[domain](entry=entry, context=context)
        except Exception as exc:
            stop(f"adapter exception for {eid}: {type(exc).__name__}: {exc}")
        if not isinstance(returned, dict) or set(returned) != set(ARMS):
            stop(f"{eid}: adapter must return exactly arms {list(ARMS)}")
        arms = {}
        for arm in ARMS:
            value = returned[arm]
            if not isinstance(value, dict) or value.get("status") not in STATUSES:
                stop(f"{eid}/{arm}: adapter must return an explicit terminal status")
            status = value["status"]
            payload = value.get("payload")
            if status == "success" and not isinstance(payload, dict):
                stop(f"{eid}/{arm}: successful arm requires payload object")
            if payload is not None and not isinstance(payload, dict):
                stop(f"{eid}/{arm}: payload must be an object")
            arms[arm] = {"status": status, **({"payload": payload} if payload is not None else {})}
        results.append({"equation_id": eid, "arms": arms})

    artifact = {
        "schema": RESULT_SCHEMA,
        "run_id": m["run_id"],
        "catalogue_sha256": m["catalogue_sha256"],
        "task_set_sha256": m["task_set_sha256"],
        "shard_id": args.shard_id,
        "shard_count": m["shard_count"],
        "equations": results,
        "provenance": {
            "manifest_sha256": sha(manifest_raw),
            "catalogue_sha256": sha(catalogue_raw),
            "driver": "core295_run_shard.py",
            "live_services_allowed": args.allow_live_services,
            "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
        }
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("xb", encoding="utf-8") as stream:
            stream.write(canonical(artifact).decode("utf-8"))
    except FileExistsError:
        stop(f"refusing to overwrite existing shard result: {args.output}")
    print(json.dumps({"status": "SHARD_COMPLETED", "run_id": m["run_id"],
                      "shard_id": args.shard_id, "equations": len(results),
                      "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
