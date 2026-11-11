#!/usr/bin/env python3
"""Validate the Core-295 catalogue manifest without running experiments.

This validator checks catalogue structure and declared review metadata. It does
not prove scientific correctness, algebraic inequivalence, or statistical
independence; those require domain review and a defensible sampling design.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "core295_catalogue.json"
DOMAINS = ("Chemistry", "Biology", "Physics", "DeFi AMM", "DeFi Risk")
ACCEPTED = "accepted"
REQUIRED_FIELDS = (
    "equation_id", "name", "domain", "subdomain", "formula",
    "canonical_expression", "structural_fingerprint", "source_ids",
    "source_family_id", "status", "assumptions", "variables",
    "validity", "input_ranges", "generator",
)


class CatalogueError(ValueError):
    pass


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate(data: dict, require_ready: bool = False) -> list[str]:
    errors: list[str] = []
    if data.get("catalogue_id") != "core295-option2":
        _fail(errors, "catalogue_id must be 'core295-option2'")
    if data.get("target_equation_count") != 295:
        _fail(errors, "target_equation_count must be 295")
    if data.get("per_domain_target") != 59:
        _fail(errors, "per_domain_target must be 59")
    if tuple(data.get("domains", ())) != DOMAINS:
        _fail(errors, f"domains must be exactly {list(DOMAINS)} in canonical order")

    excluded = data.get("core15_exclusion_ids")
    if not isinstance(excluded, list) or len(excluded) != 15 or len(set(excluded)) != 15:
        _fail(errors, "core15_exclusion_ids must contain the 15 unique Core-15 names")
    entries = data.get("entries")
    if not isinstance(entries, list):
        _fail(errors, "entries must be a list")
        entries = []

    sources = data.get("source_register", [])
    source_ids = {
        item.get("source_id") for item in sources
        if isinstance(item, dict) and isinstance(item.get("source_id"), str)
    }
    ids: set[str] = set()
    fingerprints: dict[str, str] = {}
    counts = {domain: 0 for domain in DOMAINS}
    accepted_counts = {domain: 0 for domain in DOMAINS}
    independence_ids: dict[str, str] = {}

    for index, entry in enumerate(entries):
        where = f"entries[{index}]"
        if not isinstance(entry, dict):
            _fail(errors, f"{where} must be an object")
            continue
        for field in REQUIRED_FIELDS:
            if field not in entry or entry[field] in (None, "", []):
                _fail(errors, f"{where}.{field} is required")
        equation_id = entry.get("equation_id")
        if isinstance(equation_id, str):
            if equation_id in set(excluded or []):
                _fail(errors, f"Core-15 exclusion violation: {equation_id}")
            if equation_id in ids:
                _fail(errors, f"duplicate equation_id: {equation_id}")
            ids.add(equation_id)
        domain = entry.get("domain")
        if domain not in counts:
            _fail(errors, f"{where}.domain is not one of the five Core-15 domains")
        else:
            counts[domain] += 1
            if entry.get("status") == ACCEPTED:
                accepted_counts[domain] += 1

        fp = entry.get("structural_fingerprint")
        if isinstance(fp, str) and fp:
            if not re.fullmatch(r"[0-9a-f]{64}", fp):
                _fail(errors, f"{where}.structural_fingerprint must be a lowercase SHA-256 hex digest")
            elif fp in fingerprints:
                _fail(errors, f"structural fingerprint collision: {equation_id} and {fingerprints[fp]}")
            else:
                fingerprints[fp] = str(equation_id)

        refs = entry.get("source_ids")
        if isinstance(refs, list):
            if not refs:
                _fail(errors, f"{where}.source_ids must contain at least one source")
            for source_id in refs:
                if source_id not in source_ids:
                    _fail(errors, f"{where} references unknown source_id {source_id!r}")

        if entry.get("status") not in {
            "proposed", "source_verified", "scientifically_reviewed",
            "structurally_reviewed", "accepted", "rejected"
        }:
            _fail(errors, f"{where}.status is not a recognized review state")

        if entry.get("status") == ACCEPTED:
            if not entry.get("reviewer") or not entry.get("reviewed_on"):
                _fail(errors, f"{where} accepted entry requires reviewer and reviewed_on")
            if not entry.get("equivalence_review"):
                _fail(errors, f"{where} accepted entry requires equivalence_review")
            if not entry.get("independence_unit_id"):
                _fail(errors, f"{where} accepted entry requires an explicit independence_unit_id or a documented non-eligible marker")
            else:
                unit = entry["independence_unit_id"]
                previous = independence_ids.get(unit)
                if previous and previous != entry.get("source_family_id"):
                    _fail(errors, f"independence unit {unit!r} maps to multiple source families")
                independence_ids[unit] = str(entry.get("source_family_id"))

    for domain in DOMAINS:
        if counts[domain] > 59:
            _fail(errors, f"{domain} has {counts[domain]} entries; maximum is 59")
        if require_ready and accepted_counts[domain] != 59:
            _fail(errors, f"{domain} has {accepted_counts[domain]} accepted entries; exactly 59 required")

    sampling = data.get("sampling_frame") or {}
    if require_ready:
        if data.get("status") != "ready":
            _fail(errors, "status must be 'ready' when --require-ready is used")
        for field in (
            "source_universe", "inclusion_exclusion_rules", "selection_method",
            "independent_statistical_unit", "source_family_definition"
        ):
            if not sampling.get(field):
                _fail(errors, f"sampling_frame.{field} must be frozen before readiness")
        if sampling.get("status") != "frozen":
            _fail(errors, "sampling_frame.status must be 'frozen'")
        if len(entries) != 295:
            _fail(errors, f"ready catalogue must contain exactly 295 entries, found {len(entries)}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read catalogue manifest: {exc}", file=sys.stderr)
        return 2
    errors = validate(data, require_ready=args.require_ready)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    digest = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
    print(f"Core-295 catalogue structure OK (status={data.get('status')}, entries={len(data.get('entries', []))})")
    print(f"manifest_sha256={digest}")
    if not args.require_ready:
        print("NOTE: structural validation is not scientific review or proof of independence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
