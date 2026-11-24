# Offline tau provenance-envelope verifier

**Status:** schema-v1 prototype for retained-file integrity checks. This tool does not create calibration records, run experiments, call providers, select tau, or establish scientific independence.

## Scope and claim boundary

Run `scripts/verify_tau_provenance_envelope.py` against a JSON envelope and an artifact directory. The verifier recomputes SHA-256 for every referenced evaluator source file, dependency lockfile, input artifact, and output artifact.

A successful result means only that the declared bytes are present under the supplied root and match the declared digests. It does **not** prove:

- that the Git commit exists, belongs to the declared repository, or was checked out for the run;
- that the working tree was actually clean (the field is a declaration);
- that the recorded command/runtime produced the output;
- that the evaluator was executed from the source files whose hashes are listed; or
- that any equation families are mathematically independent or properly adjudicated.

The report explicitly keeps commit resolution, execution attestation, and scientific adjudication as `not_performed`.

## Version 1 envelope

All artifact paths must use canonical, portable forward-slash relative syntax beneath `--artifact-root`: empty segments (including repeated or trailing slashes), absolute paths, `.`/`..` segments, backslashes, NULs, and drive-style colons are rejected before filesystem access. Symlinks, missing files, non-files, duplicate paths, malformed hashes, and byte/hash mismatches are also rejected. The repository URL must be a canonical HTTPS GitHub URL of the form `https://github.com/owner/repository` (no credentials, port, query, fragment, trailing slash, or `.git` suffix). This validates URL shape only; it does not resolve or verify the repository.

```json
{
  "schema_version": 1,
  "repository": {
    "url": "https://github.com/owner/repository",
    "commit": "0123456789abcdef0123456789abcdef01234567",
    "working_tree_clean": true
  },
  "evaluator": {
    "version": "tau-independent-evaluation-validator-v1",
    "source_files": [
      {"path": "source/validator.py", "sha256": "<64 lowercase hex characters>"}
    ]
  },
  "execution": {
    "python_version": "3.12.0",
    "dependency_lock": {
      "path": "requirements.lock",
      "sha256": "<64 lowercase hex characters>"
    },
    "command": "python source/run_evaluation.py",
    "arguments": ["--input", "inputs/frozen.json"]
  },
  "inputs": [
    {"path": "inputs/frozen.json", "sha256": "<64 lowercase hex characters>"}
  ],
  "output": {
    "path": "outputs/report.json",
    "sha256": "<64 lowercase hex characters>"
  }
}
```

The repository URL and all other values above are illustrative placeholders, not a valid evidence package. The referenced files must exist and their actual SHA-256 values must be supplied. The envelope itself should be retained alongside the artifacts; its digest and immutable storage location belong in the surrounding run record.

## CLI

```bash
python scripts/verify_tau_provenance_envelope.py \\
  --envelope provenance-envelope.json \\
  --artifact-root frozen-artifacts/ \\
  --report provenance-verification.json
```

Exit codes:

- `0`: every declared artifact digest and schema check passed;
- `1`: envelope or artifact validation failed;
- `2`: envelope/report I/O or JSON parsing failed.

## Security and retention notes

- Use a dedicated, immutable artifact directory for each frozen run.
- Preserve the envelope, every referenced file, and the verification report together.
- Do not place secrets, tokens, credentials, or private keys in command arguments or the envelope.
- Hash the exact bytes; do not normalize JSON, line endings, or formulas before hashing unless a separate canonicalization specification is versioned.
- This prototype rejects symlinks and path escapes, but it is not a sandbox against concurrent mutation of the artifact directory. Verify from a read-only snapshot or immutable artifact store for production use.
- The declared output digest must be computed after the output is finalized. The verifier does not write or modify the output artifact.

## Follow-on gates

A later, separately reviewed layer may resolve commit IDs against a pinned repository, verify repository identity and source-tree membership, and bind execution attestations to immutable run records. Those features must be implemented and tested as distinct checks. Do not change the existing calibration or independent-evaluation risk tests to accommodate this prototype, and do not infer readiness from an artifact-integrity pass.
