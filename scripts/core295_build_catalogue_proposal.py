#!/usr/bin/env python3
"""Build a non-applying Core-295 catalogue proposal from audited staged records.

The command reruns the read-only staged-promotion audit, then writes a proposed
catalogue snapshot and unified diff. It never edits the canonical catalogue,
never marks a candidate accepted, and refuses to overwrite proposal files.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path
from difflib import unified_diff

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts/core295_audit_staged_promotions.py"

def read_bytes(path):
    return path.read_bytes()

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def load_json(path):
    return json.loads(read_bytes(path).decode("utf-8"))

def staging_snapshot(directory):
    if not directory.exists():
        return {}
    return {str(path.resolve()): sha256(read_bytes(path))
            for path in sorted(directory.rglob("*.json"))}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalogue", type=Path, default=ROOT / "config/core295_catalogue.json")
    p.add_argument("--staging-dir", type=Path, default=ROOT / "data/core295_staging")
    p.add_argument("--output", type=Path, required=True, help="new proposed catalogue JSON")
    p.add_argument("--diff", type=Path, required=True, help="new unified diff output")
    a = p.parse_args()
    if a.output.exists() or a.diff.exists():
        p.error("proposal output already exists; refusing to overwrite")
    if a.output.resolve() == a.diff.resolve():
        p.error("--output and --diff must be different files")

    try:
        original_bytes = read_bytes(a.catalogue)
        catalogue = json.loads(original_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        p.error("cannot read canonical catalogue: " + str(exc))
    if not isinstance(catalogue, dict) or not isinstance(catalogue.get("entries"), list):
        p.error("catalogue must contain an entries array")

    staged_snapshot_before = staging_snapshot(a.staging_dir)
    cmd = [sys.executable, str(AUDIT), "--catalogue", str(a.catalogue),
           "--staging-dir", str(a.staging_dir), "--stdout"]
    audit = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if audit.returncode != 0:
        print("BLOCKED: staged-promotion audit returned nonzero.")
        print(audit.stdout)
        print(audit.stderr)
        return 2
    summary = re.search(r"staged=(\d+)\s+blockers=(\d+)\s+errors=(\d+)\s+warnings=(\d+)", audit.stdout)
    if not summary:
        print("BLOCKED: could not parse audit summary; no proposal written.")
        print(audit.stdout)
        return 2
    staged_count, blockers, errors, warnings = map(int, summary.groups())
    if sha256(read_bytes(a.catalogue)) != sha256(original_bytes):
        print("BLOCKED: canonical catalogue changed while the audit was running.")
        return 2
    staged_snapshot_after = staging_snapshot(a.staging_dir)
    if staged_snapshot_after != staged_snapshot_before:
        print("BLOCKED: staged inputs changed while the audit was running.")
        return 2
    if staged_count < 1:
        print("BLOCKED: no staged candidate records found; no proposal written.")
        return 2
    if blockers or errors:
        print(f"BLOCKED: audit found {blockers} blocker(s) and {errors} error(s); no proposal written.")
        print(audit.stdout)
        return 2

    staged_paths = sorted(a.staging_dir.rglob("*.json"))
    staged_rows = []
    for path in staged_paths:
        try:
            row = load_json(path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            print("BLOCKED: staged JSON changed or became unreadable: " + str(path) + ": " + str(exc))
            return 2
        if not isinstance(row, dict) or row.get("status") != "structurally_reviewed":
            print("BLOCKED: unexpected staged record during proposal assembly: " + str(path))
            return 2
        staged_rows.append((path, row))

    # Ensure staged set still agrees with the audit count and no IDs collide.
    if len(staged_rows) != staged_count:
        print("BLOCKED: staged record count changed between audit and proposal assembly.")
        return 2
    ids = [str(row.get("equation_id") or "") for _, row in staged_rows]
    if len(set(ids)) != len(ids) or any(not x for x in ids):
        print("BLOCKED: staged equation IDs are missing or duplicated.")
        return 2

    proposal = json.loads(json.dumps(catalogue))
    existing_ids = {str(x.get("equation_id")) for x in proposal["entries"] if x.get("equation_id")}
    if existing_ids.intersection(ids):
        print("BLOCKED: staged equation ID now exists in canonical catalogue.")
        return 2
    before_counts = {domain: sum(1 for x in proposal["entries"]
                                 if x.get("domain") == domain and x.get("status") == "accepted")
                     for domain in proposal.get("domains", [])}
    appended = []
    for path, row in staged_rows:
        # Strip helper-only metadata; retain reviewer/equivalence traceability.
        entry = {k: v for k, v in row.items() if not k.startswith("_")}
        entry["status"] = "structurally_reviewed"
        entry.pop("accepted", None)
        appended.append(entry)
    proposal["entries"].extend(appended)
    proposal["status"] = "draft"

    manifest = {
        "proposal_version": "1.0",
        "proposal_type": "append_structurally_reviewed_candidates",
        "canonical_catalogue_path": str(a.catalogue),
        "canonical_catalogue_sha256": sha256(original_bytes),
        "staging_directory": str(a.staging_dir),
        "staged_inputs": [{"path": str(path), "sha256": sha256(read_bytes(path)),
                           "equation_id": row.get("equation_id")}
                          for path, row in staged_rows],
        "audit_summary": {"staged": staged_count, "blockers": blockers,
                          "errors": errors, "warnings": warnings},
        "accepted_count_by_domain_before": before_counts,
        "appended_equation_ids": ids,
        "resulting_catalogue_status": "draft",
        "acceptance_performed": False,
        "canonical_catalogue_modified": False,
        "maintainer_signoff": None,
        "notice": "Proposal only. Inspect the diff, re-check source evidence and catalogue-wide structural/sampling implications. A maintainer must explicitly approve and separately apply any change. No equation is accepted by this tool."
    }
    proposal["promotion_proposal"] = manifest

    old_text = original_bytes.decode("utf-8").splitlines(keepends=True)
    new_text = (json.dumps(proposal, indent=2, ensure_ascii=False) + "\n").splitlines(keepends=True)
    diff_text = "".join(unified_diff(old_text, new_text,
                                    fromfile=str(a.catalogue) + " (canonical)",
                                    tofile=str(a.output) + " (proposal)"))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.diff.parent.mkdir(parents=True, exist_ok=True)
    try:
        with a.output.open("x", encoding="utf-8") as f:
            json.dump(proposal, f, indent=2, ensure_ascii=False)
            f.write("\n")
        with a.diff.open("x", encoding="utf-8") as f:
            f.write(diff_text)
    except OSError as exc:
        print("ERROR writing proposal outputs: " + str(exc))
        print("If only one output was created, inspect and remove it manually before retrying.")
        return 1
    print("Wrote proposed catalogue snapshot: " + str(a.output))
    print("Wrote unified diff: " + str(a.diff))
    print(f"staged={staged_count} blockers=0 errors=0 warnings={warnings}")
    print("Canonical catalogue unchanged; resulting status=draft; accepted flags were not set.")
    print("This proposal is not scientific approval or authorization to apply the diff.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
