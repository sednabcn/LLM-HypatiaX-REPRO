#!/usr/bin/env python3
"""Apply an explicitly approved Core-295 proposal with hash, backup and validation gates.

This command is intentionally inert unless --apply is supplied. It is not a
scientific approval mechanism; the approval JSON is a human attestation.
"""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_core295_catalogue.py"
REQUIRED_CONFIRMATIONS = (
    "primary_source_pages_inspected",
    "transcriptions_checked_against_source",
    "structural_equivalence_review_checked",
    "source_family_and_independence_units_checked",
    "sampling_frame_implications_checked",
    "all_findings_resolved_or_documented",
)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def fail(message: str) -> int:
    print("BLOCKED: " + message, file=sys.stderr)
    return 2

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--proposal", type=Path, required=True)
    p.add_argument("--diff", type=Path, required=True)
    p.add_argument("--approval", type=Path, required=True)
    p.add_argument("--catalogue", type=Path, default=ROOT / "config/core295_catalogue.json")
    p.add_argument("--backup", type=Path, required=True)
    p.add_argument("--apply", action="store_true", help="explicitly authorize file replacement after all gates pass")
    a = p.parse_args()
    if not a.apply:
        return fail("dry inspection only; pass --apply only after explicit maintainer authorization")
    for path in (a.proposal, a.diff, a.approval, a.catalogue):
        if not path.is_file():
            return fail("required file does not exist: " + str(path))
    if a.backup.exists():
        return fail("backup path already exists; refusing to overwrite it")
    try:
        original = a.catalogue.read_bytes()
        proposal_bytes = a.proposal.read_bytes()
        diff_bytes = a.diff.read_bytes()
        proposal = json.loads(proposal_bytes.decode("utf-8"))
        approval = load(a.approval)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return fail("cannot read inputs: " + str(exc))

    manifest = proposal.get("promotion_proposal") if isinstance(proposal, dict) else None
    if not isinstance(manifest, dict):
        return fail("proposal lacks promotion_proposal provenance manifest")
    if manifest.get("acceptance_performed") is not False or manifest.get("canonical_catalogue_modified") is not False:
        return fail("proposal manifest does not declare a non-accepting, non-applying build")
    if proposal.get("status") != "draft":
        return fail("proposal catalogue status must remain draft")
    if digest(original) != manifest.get("canonical_catalogue_sha256"):
        return fail("canonical catalogue no longer matches the proposal's source hash")
    if digest(original) != approval.get("canonical_catalogue_sha256_before"):
        return fail("approval record canonical hash does not match current catalogue")
    if digest(proposal_bytes) != approval.get("proposal_sha256"):
        return fail("approval record proposal hash mismatch")
    if digest(diff_bytes) != approval.get("diff_sha256"):
        return fail("approval record diff hash mismatch")
    if str(a.proposal) != manifest.get("canonical_catalogue_path") and Path(manifest.get("canonical_catalogue_path","")).name != a.catalogue.name:
        return fail("proposal canonical path does not match target catalogue")
    if approval.get("decision") != "approve":
        return fail("approval decision must be exactly 'approve'")
    if approval.get("proposal_path") != str(a.proposal) or approval.get("diff_path") != str(a.diff):
        return fail("approval paths must match the exact proposal and diff arguments")
    if approval.get("canonical_catalogue_path") != str(a.catalogue):
        return fail("approval canonical path does not match target")
    approved_ids = approval.get("approved_appended_equation_ids")
    proposed_ids = manifest.get("appended_equation_ids")
    if not isinstance(approved_ids, list) or approved_ids != proposed_ids:
        return fail("approved equation ID list must exactly match proposal order and contents")
    warnings = (manifest.get("audit_summary") or {}).get("warnings", 0)
    if warnings and not approval.get("audit_warnings_disposition"):
        return fail("audit warnings require explicit disposition in approval record")
    confirmations = approval.get("scientific_review_confirmation") or {}
    if any(confirmations.get(k) is not True for k in REQUIRED_CONFIRMATIONS):
        return fail("all scientific-review confirmations must be explicitly true")
    for key in ("maintainer_approval", "second_maintainer_approval"):
        person = approval.get(key) or {}
        if not person.get("name_or_account") or not person.get("role") or not person.get("approval_statement"):
            return fail(key + " must identify approver, role and approval statement")
        if not person.get("approved_on") or person.get("approved_on") == "YYYY-MM-DD":
            return fail(key + " requires an approval date")
    if approval["maintainer_approval"]["name_or_account"] == approval["second_maintainer_approval"]["name_or_account"]:
        return fail("two distinct maintainer approvers are required")
    auth = approval.get("application_authorization") or {}
    if auth.get("authorized") is not True or not auth.get("authorized_by") or not auth.get("authorized_on"):
        return fail("explicit application authorization, authorizer and date are required")
    if auth.get("exact_canonical_path") != str(a.catalogue):
        return fail("application authorization must name the exact canonical path")

    before_entries = load(a.catalogue).get("entries", [])
    after_entries = proposal.get("entries", [])
    if len(after_entries) != len(before_entries) + len(proposed_ids):
        return fail("proposal entry-count change does not match appended ID list")
    old_ids = {x.get("equation_id") for x in before_entries if isinstance(x, dict)}
    new_rows = [x for x in after_entries if isinstance(x, dict) and x.get("equation_id") not in old_ids]
    if [x.get("equation_id") for x in new_rows] != proposed_ids:
        return fail("proposal entries are not exactly the approved append-only ID sequence")
    if any(x.get("status") != "structurally_reviewed" or x.get("accepted") is True for x in new_rows):
        return fail("new entries must remain structurally_reviewed and not accepted")
    if any(x.get("status") != y.get("status") or x.get("equation_id") != y.get("equation_id")
           for x, y in zip(before_entries, after_entries[:len(before_entries)])):
        return fail("proposal modifies or reorders existing catalogue entries")

    # Validate the proposed file before touching the canonical path.
    with tempfile.NamedTemporaryFile("wb", suffix=".json", dir=a.catalogue.parent, delete=False) as tmp:
        temp_path = Path(tmp.name)
        tmp.write(proposal_bytes)
        tmp.flush()
        os.fsync(tmp.fileno())
    try:
        check = subprocess.run([sys.executable, str(VALIDATOR), "--manifest", str(temp_path)],
                               cwd=ROOT, capture_output=True, text=True, check=False)
    finally:
        temp_path.unlink(missing_ok=True)
    if check.returncode != 0:
        print(check.stdout)
        print(check.stderr, file=sys.stderr)
        return fail("catalogue structural validator rejected proposal")

    # Recheck immediately before replacement; backup is exclusive and exact.
    if digest(a.catalogue.read_bytes()) != digest(original):
        return fail("canonical catalogue changed during approval checks")
    a.backup.parent.mkdir(parents=True, exist_ok=True)
    try:
        with a.backup.open("xb") as f:
            f.write(original)
            f.flush()
            os.fsync(f.fileno())
        fd, temp_name = tempfile.mkstemp(prefix=a.catalogue.name + ".", suffix=".tmp",
                                         dir=a.catalogue.parent)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(proposal_bytes)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_name, a.catalogue)
        except Exception:
            Path(temp_name).unlink(missing_ok=True)
            raise
    except OSError as exc:
        return fail("application failed; inspect backup and target before retrying: " + str(exc))
    print("Applied approved proposal to: " + str(a.catalogue))
    print("Exact pre-application backup: " + str(a.backup))
    print("New catalogue SHA-256: " + digest(a.catalogue.read_bytes()))
    print("Catalogue remains draft; appended records remain structurally_reviewed, not accepted.")
    print("This file operation does not constitute scientific acceptance or experiment execution.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
