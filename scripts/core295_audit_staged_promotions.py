#!/usr/bin/env python3
"""Audit staged Core-295 candidates against the catalogue and source register.

Read-only with respect to scientific records: emits reports only; never edits or
promotes catalogue entries. Findings are triage flags, not scientific judgments.
"""
from __future__ import annotations
import argparse, json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOGUE = ROOT / "config/core295_catalogue.json"
DEFAULT_STAGING = ROOT / "data/core295_staging"
DEFAULT_REPORT = ROOT / "data/core295_promotion_audit.md"
DOMAINS = ("Chemistry", "Biology", "Physics", "DeFi AMM", "DeFi Risk")

def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def read_staged(directory):
    rows, errors = [], []
    if not directory.exists():
        return rows, errors
    for path in sorted(directory.rglob("*.json")):
        try:
            item = load_json(path)
            if not isinstance(item, dict):
                errors.append((str(path), "top-level JSON value is not an object"))
                continue
            rows.append((path, item))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append((str(path), str(exc)))
    return rows, errors

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    p.add_argument("--staging-dir", type=Path, default=DEFAULT_STAGING)
    p.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    p.add_argument("--stdout", action="store_true")
    a = p.parse_args()
    try:
        catalogue = load_json(a.catalogue)
    except (OSError, json.JSONDecodeError) as exc:
        p.error("cannot read catalogue: " + str(exc))
    if not isinstance(catalogue, dict) or not isinstance(catalogue.get("entries"), list):
        p.error("catalogue must contain an entries array")
    source_register = catalogue.get("source_register", [])
    if not isinstance(source_register, list):
        p.error("catalogue source_register must be an array")

    source_rows = defaultdict(list)
    for item in source_register:
        if isinstance(item, dict) and item.get("source_id"):
            source_rows[str(item["source_id"])].append(item)
    sources = {sid: rows[0] for sid, rows in source_rows.items()}
    existing = catalogue["entries"]
    existing_ids = {str(x.get("equation_id")): x for x in existing if x.get("equation_id")}
    existing_fps = defaultdict(list)
    source_users = defaultdict(list)
    family_domains = defaultdict(set)
    unit_families = defaultdict(set)
    for row in existing:
        eid = str(row.get("equation_id") or "<missing-id>")
        fp = row.get("structural_fingerprint")
        if fp: existing_fps[str(fp)].append(eid)
        for sid in row.get("source_ids", []) if isinstance(row.get("source_ids"), list) else []:
            source_users[str(sid)].append(eid)
        fam = row.get("source_family_id")
        if fam: family_domains[str(fam)].add(str(row.get("domain")))
        unit = row.get("independence_unit_id")
        if unit and unit != "not_eligible":
            unit_families[str(unit)].add(str(fam or "<missing-family>"))

    staged, read_errors = read_staged(a.staging_dir)
    findings = []
    def add(level, path, code, detail):
        findings.append({"level": level, "path": str(path), "code": code, "detail": detail})

    for path, msg in read_errors:
        add("ERROR", path, "INVALID_STAGING_JSON", msg)

    staged_ids, staged_fps, staged_units, staged_sources = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for sid, rows in source_rows.items():
        if len(rows) > 1:
            add("ERROR", a.catalogue, "DUPLICATE_SOURCE_REGISTER_ID", sid + " occurs " + str(len(rows)) + " times in source_register")
    for path, row in staged:
        eid = str(row.get("equation_id") or "")
        if not eid: add("ERROR", path, "MISSING_EQUATION_ID", "staged record has no equation_id")
        else:
            staged_ids[eid].append(str(path))
            if eid in existing_ids:
                add("BLOCKER", path, "EQUATION_ID_ALREADY_IN_CATALOGUE", eid)
        if row.get("status") != "structurally_reviewed":
            add("BLOCKER", path, "STAGED_STATUS_INVALID", "expected structurally_reviewed; found " + str(row.get("status")))
        if row.get("accepted") is True or row.get("status") == "accepted":
            add("BLOCKER", path, "ACCEPTED_FLAG_FORBIDDEN", "staging audit never authorizes acceptance")
        if row.get("_promotion_notice") is None:
            add("WARNING", path, "MISSING_STAGING_NOTICE", "record lacks staging-only notice")
        domain = row.get("domain")
        if domain not in DOMAINS:
            add("ERROR", path, "INVALID_DOMAIN", str(domain))
        fp = row.get("structural_fingerprint")
        if fp:
            staged_fps[str(fp)].append((path, eid))
            if str(fp) in existing_fps:
                add("BLOCKER", path, "FINGERPRINT_MATCHES_CATALOGUE",
                    "same fingerprint as " + ", ".join(existing_fps[str(fp)]))
        family = str(row.get("source_family_id") or "")
        if family and domain:
            if family in family_domains and domain not in family_domains[family]:
                add("WARNING", path, "SOURCE_FAMILY_CROSSES_DOMAINS",
                    family + " already appears in " + ", ".join(sorted(family_domains[family])))
        unit = str(row.get("independence_unit_id") or "")
        if unit:
            staged_units[unit].append((path, family))
            previous = unit_families.get(unit, set())
            if previous and family not in previous:
                add("BLOCKER", path, "STATISTICAL_UNIT_FAMILY_CONFLICT",
                    unit + " already maps to " + ", ".join(sorted(previous)))
        sids = row.get("source_ids")
        if not isinstance(sids, list) or not sids:
            add("ERROR", path, "SOURCE_IDS_EMPTY", "at least one source_id is required")
        else:
            for sid in sids:
                staged_sources[str(sid)].append((path, eid))
                if str(sid) not in sources:
                    add("BLOCKER", path, "SOURCE_ID_NOT_IN_REGISTER", str(sid))
                else:
                    src = sources[str(sid)]
                    if src.get("domain") and domain and src["domain"] != domain:
                        add("WARNING", path, "SOURCE_DOMAIN_MISMATCH",
                            str(sid) + " registered as " + str(src.get("domain")) + ", candidate is " + str(domain))
        decision = row.get("human_review_decision") or {}
        if decision.get("candidate_equation_id") != eid:
            add("ERROR", path, "DECISION_CANDIDATE_MISMATCH", "embedded decision does not identify staged equation_id")
        if decision.get("structural_equivalence", {}).get("classification") != "E4":
            add("BLOCKER", path, "DECISION_NOT_E4", "embedded decision must record E4")
        reviewers = {str(decision.get("primary_reviewer") or "").strip().casefold(),
                     str(decision.get("second_reviewer") or "").strip().casefold()}
        if "" in reviewers or len(reviewers) != 2:
            add("BLOCKER", path, "REVIEWER_INDEPENDENCE_MISSING", "two distinct named reviewers required")
        if row.get("equivalence_review", {}).get("classification") != "E4":
            add("BLOCKER", path, "CATALOGUE_EQUIVALENCE_NOT_E4", "staged equivalence_review must be E4")
        if not row.get("independence_unit_id"):
            add("BLOCKER", path, "INDEPENDENCE_UNIT_MISSING", "independence_unit_id is required")

    for eid, paths in staged_ids.items():
        if len(paths) > 1:
            for path in paths:
                add("BLOCKER", path, "DUPLICATE_STAGED_EQUATION_ID", eid + " appears in " + ", ".join(paths))
    for fp, records in staged_fps.items():
        if len(records) > 1:
            for path, eid in records:
                add("BLOCKER", path, "DUPLICATE_STAGED_FINGERPRINT",
                    fp + " shared by " + ", ".join(x[1] for x in records))
    for sid, records in staged_sources.items():
        if len(records) > 1:
            for path, eid in records:
                add("WARNING", path, "SOURCE_ID_SHARED_BY_STAGED_CANDIDATES",
                    sid + " is cited by staged candidates " + ", ".join(x[1] for x in records) +
                    "; confirm this shared source is intentional and does not imply a common model family")
    for unit, records in staged_units.items():
        fams = {family for _, family in records}
        if len(fams) > 1:
            for path, _ in records:
                add("BLOCKER", path, "STAGED_UNIT_FAMILY_CONFLICT",
                    unit + " assigned to multiple source families: " + ", ".join(sorted(fams)))

    blockers = sum(x["level"] == "BLOCKER" for x in findings)
    errors = sum(x["level"] == "ERROR" for x in findings)
    warnings = sum(x["level"] == "WARNING" for x in findings)
    lines = [
        "# Core-295 staged-candidate promotion audit", "",
        "- Catalogue: " + str(a.catalogue),
        "- Staging directory: " + str(a.staging_dir),
        "- Catalogue entries: " + str(len(existing)),
        "- Registered source IDs: " + str(len(sources)),
        "- Staged JSON records: " + str(len(staged)),
        "- Read errors: " + str(len(read_errors)),
        "- Blockers / errors / warnings: " + f"{blockers} / {errors} / {warnings}", "",
        "**Read-only audit. No catalogue entries were changed, accepted, or promoted.**",
        "Findings are consistency flags, not proof of scientific correctness, structural inequivalence or statistical independence.", "",
        "## Findings", ""
    ]
    if not findings:
        lines.append("No mechanical consistency findings. This is not approval to promote or accept a candidate.")
    else:
        lines += ["| Level | Candidate file | Check | Detail |", "|---|---|---|---|"]
        for x in findings:
            detail = x["detail"].replace("|", r"\|").replace("\n", " ")
            lines.append("| " + x["level"] + " | " + x["path"].replace("|", r"\|") +
                         " | " + x["code"] + " | " + detail + " |")
    lines += ["", "## Required maintainer review", "",
        "1. Inspect each primary source at the cited page/version and verify the full governing model.",
        "2. Re-run pairwise structural review against all proposed and accepted candidates, including cross-domain analogues and Core-15 exclusions.",
        "3. Confirm source-family and statistical-unit assignments against the frozen sampling design.",
        "4. Resolve every blocker/error and document any warning disposition.",
        "5. Only a separate, explicit maintainer decision may change the canonical catalogue; this report never does so.", ""]
    report = "\n".join(lines)
    if a.stdout:
        print(report)
    else:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with a.output.open("x", encoding="utf-8") as f:
            f.write(report)
        print("Wrote read-only promotion audit: " + str(a.output))
    print(f"staged={len(staged)} blockers={blockers} errors={errors} warnings={warnings}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
