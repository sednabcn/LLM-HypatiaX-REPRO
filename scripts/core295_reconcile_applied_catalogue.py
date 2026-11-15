#!/usr/bin/env python3
"""Reconcile an applied Core-295 catalogue against its approved proposal and backup.

Read-only. Verifies hashes, approved IDs, append-only integrity and review states.
Does not change the catalogue or any scientific/review status.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalogue", type=Path, required=True)
    p.add_argument("--proposal", type=Path, required=True)
    p.add_argument("--diff", type=Path, required=True)
    p.add_argument("--approval", type=Path, required=True)
    p.add_argument("--backup", type=Path, required=True)
    p.add_argument("--report", type=Path, help="optional new Markdown report; refuses overwrite")
    a = p.parse_args()
    errors, warnings, checks = [], [], []
    for path in (a.catalogue, a.proposal, a.diff, a.approval, a.backup):
        if not path.is_file():
            errors.append("missing required file: " + str(path))
    if errors:
        for e in errors: print("ERROR: " + e)
        return 2
    try:
        current, proposed, approval = load(a.catalogue), load(a.proposal), load(a.approval)
        backup_bytes = a.backup.read_bytes()
        backup = json.loads(backup_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print("ERROR: unable to parse reconciliation inputs: " + str(exc), file=sys.stderr)
        return 2

    if not all(isinstance(x, dict) for x in (current, proposed, approval, backup)):
        print("ERROR: catalogue, proposal, approval and backup must each be JSON objects.", file=sys.stderr)
        return 2
    current_hash, proposal_hash, diff_hash = sha(a.catalogue), sha(a.proposal), sha(a.diff)
    backup_hash = hashlib.sha256(backup_bytes).hexdigest()
    manifest = proposed.get("promotion_proposal")
    if not isinstance(manifest, dict):
        print("ERROR: proposal is missing its promotion_proposal manifest.", file=sys.stderr)
        return 2
    ids = manifest.get("appended_equation_ids")
    approval_ids = approval.get("approved_appended_equation_ids")
    if not isinstance(ids, list) or not all(isinstance(x, str) and x for x in ids):
        print("ERROR: proposal appended_equation_ids must be a list of non-empty strings.", file=sys.stderr)
        return 2
    if not isinstance(approval_ids, list):
        print("ERROR: approval approved_appended_equation_ids must be a list.", file=sys.stderr)
        return 2

    def check(name, condition, detail):
        checks.append((name, bool(condition), detail))
        if not condition: errors.append(name + ": " + detail)

    check("approval decision", approval.get("decision") == "approve", "approval must be approve")
    check("proposal hash", proposal_hash == approval.get("proposal_sha256"), "proposal SHA-256 differs from approval record")
    check("diff hash", diff_hash == approval.get("diff_sha256"), "diff SHA-256 differs from approval record")
    check("backup hash", backup_hash == approval.get("canonical_catalogue_sha256_before") == manifest.get("canonical_catalogue_sha256"),
          "backup differs from approval or proposal's original catalogue hash")
    check("approval paths", approval.get("proposal_path") == str(a.proposal)
          and approval.get("diff_path") == str(a.diff)
          and approval.get("canonical_catalogue_path") == str(a.catalogue),
          "approval paths do not match reconciliation arguments")
    check("proposal type", manifest.get("proposal_type") == "append_structurally_reviewed_candidates",
          "unexpected or missing proposal type")
    check("proposal remains non-accepting", manifest.get("acceptance_performed") is False
          and proposed.get("status") == "draft", "proposal must declare no acceptance and remain draft")
    check("approved IDs", isinstance(ids, list) and ids == approval_ids,
          "approved IDs differ from proposal manifest")
    check("application authorization", (approval.get("application_authorization") or {}).get("authorized") is True,
          "separate application authorization is absent")
    check("current bytes equal proposal", current_hash == proposal_hash,
          "current catalogue is not byte-identical to approved proposal")
    check("current status", current.get("status") == "draft", "catalogue status is not draft")

    before = backup.get("entries", [])
    after = current.get("entries", [])
    check("append-only count", len(after) == len(before) + len(ids),
          "entry count does not equal backup entries plus approved IDs")
    check("original entries preserved", after[:len(before)] == before,
          "original entries changed or moved")
    appended = after[len(before):] if len(after) >= len(before) else []
    check("appended ID sequence", [x.get("equation_id") for x in appended] == ids,
          "appended entries differ from approved ID sequence")
    check("appended review states", all(x.get("status") == "structurally_reviewed" and x.get("accepted") is not True
                                        for x in appended),
          "appended entries must remain structurally_reviewed and not accepted")
    first = approval.get("maintainer_approval") or {}
    second = approval.get("second_maintainer_approval") or {}
    check("two distinct maintainers", bool(first.get("name_or_account"))
          and bool(second.get("name_or_account"))
          and first.get("name_or_account") != second.get("name_or_account"),
          "two distinct named maintainers are not recorded")
    if manifest.get("audit_summary", {}).get("warnings", 0):
        warnings.append("proposal carried staged-audit warnings; inspect their disposition in the approval record")
    check("proposal provenance manifest", current.get("promotion_proposal") == manifest,
          "current catalogue provenance manifest differs from approved proposal")

    report = [
        "# Core-295 post-application reconciliation", "",
        "Catalogue: " + str(a.catalogue),
        "Current catalogue SHA-256: " + current_hash,
        "Approved proposal SHA-256: " + proposal_hash,
        "Diff SHA-256: " + diff_hash,
        "Pre-application backup SHA-256: " + backup_hash,
        "Approved appended IDs: " + str(len(ids) if isinstance(ids, list) else "invalid"),
        "Result: " + ("PASS" if not errors else "FAIL"), "",
        "## Checks", "",
    ]
    report.extend("- " + ("PASS" if ok else "FAIL") + " — " + name + ": " + detail
                  for name, ok, detail in checks)
    if warnings:
        report += ["", "## Warnings", ""] + ["- " + w for w in warnings]
    if errors:
        report += ["", "## Errors", ""] + ["- " + e for e in errors]
    report += ["", "This is byte/provenance/structure reconciliation only. It does not certify scientific correctness, equation inequivalence, statistical independence, reviewer honesty, or experimental validity. It does not modify files or statuses.", ""]
    rendered = "\n".join(report)
    print(rendered)
    if a.report:
        if a.report.exists():
            print("ERROR: report path exists; refusing to overwrite: " + str(a.report), file=sys.stderr)
            return 2
        a.report.parent.mkdir(parents=True, exist_ok=True)
        try:
            with a.report.open("x", encoding="utf-8") as f: f.write(rendered)
        except OSError as exc:
            print("ERROR: could not write report: " + str(exc), file=sys.stderr)
            return 2
        print("Report written: " + str(a.report))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
