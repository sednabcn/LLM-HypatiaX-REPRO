#!/usr/bin/env python3
"""Validate human review gates and stage (never accept) one Core-295 catalogue entry."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

REQUIRED_GATES = (
    "source_verification", "equation_transcription", "variables_units_assumptions",
    "complete_model_boundary", "core15_overlap", "benchmark_generator",
    "independent_second_review",
)
CATALOGUE_FIELDS = (
    "equation_id", "name", "domain", "subdomain", "formula",
    "canonical_expression", "structural_fingerprint", "source_ids",
    "source_family_id", "assumptions", "variables", "validity",
    "input_ranges", "generator",
)

def load(path):
    with path.open(encoding="utf-8") as f: return json.load(f)

def fail(errors, message): errors.append(message)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate", type=Path, required=True,
                   help="completed candidate JSON based on the candidate-record template")
    p.add_argument("--decision", type=Path, required=True,
                   help="completed human review decision JSON")
    p.add_argument("--output", type=Path, required=True,
                   help="new staging JSON path; existing files are never overwritten")
    a = p.parse_args()
    try:
        candidate, decision = load(a.candidate), load(a.decision)
    except (OSError, json.JSONDecodeError) as exc:
        p.error("cannot read input JSON: " + str(exc))

    errors = []
    if candidate.get("_template_notice"):
        fail(errors, "candidate still contains _template_notice; complete a real candidate record")
    if decision.get("_template_notice"):
        fail(errors, "decision still contains _template_notice; complete human review")
    if decision.get("decision_status") != "ready_for_structural_review":
        fail(errors, "decision_status must be ready_for_structural_review")
    if decision.get("final_disposition") != "ready_for_structural_review":
        fail(errors, "final_disposition must be ready_for_structural_review")
    for gate in REQUIRED_GATES:
        record = decision.get(gate) or {}
        if record.get("decision") != "pass":
            fail(errors, gate + " must explicitly pass")
        if not record.get("reviewer") or not record.get("reviewed_on_utc") or not record.get("evidence"):
            fail(errors, gate + " requires reviewer, UTC date and evidence")
    eq = decision.get("structural_equivalence") or {}
    if eq.get("classification") != "E4":
        fail(errors, "only E4 can be staged as structurally reviewed under the strict draft policy")
    if not eq.get("reviewer") or not eq.get("reviewed_on_utc") or not eq.get("rationale"):
        fail(errors, "E4 decision requires reviewer, date and rationale")
    family = decision.get("source_family") or {}
    unit = decision.get("statistical_unit") or {}
    if not family.get("source_family_id") or not family.get("rationale") or not family.get("reviewer"):
        fail(errors, "source-family assignment requires ID, rationale and reviewer")
    if not unit.get("independence_unit_id") or not unit.get("rationale") or not unit.get("reviewer"):
        fail(errors, "statistical-unit assignment requires ID, rationale and reviewer")
    primary = str(decision.get("primary_reviewer") or "").strip()
    second = str(decision.get("second_reviewer") or "").strip()
    if not primary or not second or primary.casefold() == second.casefold():
        fail(errors, "distinct primary and independent second reviewers are required")
    if not decision.get("primary_reviewed_on_utc") or not decision.get("second_reviewed_on_utc"):
        fail(errors, "primary and second review UTC dates are required")
    for field in CATALOGUE_FIELDS:
        value = candidate.get(field)
        if field == "assumptions" and not value:
            value = (candidate.get("model_definition") or {}).get("assumptions")
        if value is None or value == "" or value == [] or value == {}:
            fail(errors, "candidate field missing/incomplete: " + field)
    if candidate.get("domain") not in ("Chemistry", "Biology", "Physics", "DeFi AMM", "DeFi Risk"):
        fail(errors, "candidate domain is not one of the five Core-295 domains")
    if not re.fullmatch(r"[0-9a-f]{64}", str(candidate.get("structural_fingerprint") or "")):
        fail(errors, "structural_fingerprint must be a lowercase SHA-256 digest")
    if candidate.get("status") == "accepted":
        fail(errors, "input candidate must not already be marked accepted")
    if a.output.exists():
        fail(errors, "output already exists; refusing to overwrite staged review evidence")
    if errors:
        for error in errors: print("BLOCKED: " + error)
        print("No output written. Resolve every item and obtain independent human sign-off.")
        return 1

    # Copy only catalogue fields from candidate, then attach review traceability.
    staged = {key: candidate.get(key) for key in CATALOGUE_FIELDS}
    if not staged.get("assumptions"):
        staged["assumptions"] = (candidate.get("model_definition") or {}).get("assumptions", [])
    staged["status"] = "structurally_reviewed"
    staged["reviewer"] = primary
    staged["reviewed_on"] = decision["primary_reviewed_on_utc"]
    staged["independence_unit_id"] = unit["independence_unit_id"]
    staged["equivalence_review"] = {
        "classification": "E4",
        "compared_candidates": eq.get("compared_candidates", []),
        "rationale": eq["rationale"],
        "reviewer": eq["reviewer"],
        "reviewed_on": eq["reviewed_on_utc"],
        "independent_reviewer": second,
        "independent_reviewed_on": decision["second_reviewed_on_utc"],
    }
    staged["human_review_decision"] = decision
    staged["_promotion_notice"] = (
        "Staging artifact only. Not inserted into the canonical catalogue and not accepted. "
        "A repository maintainer must inspect this record, validate source_ids against the source register, "
        "review catalogue-wide equivalence and sampling-frame implications, then explicitly approve any catalogue edit."
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x", encoding="utf-8") as f:
        json.dump(staged, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("Staged structurally_reviewed entry: " + str(a.output))
    print("Status remains structurally_reviewed; accepted=false; canonical catalogue unchanged.")
    print("This script did not verify scientific claims or run the catalogue validator.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
