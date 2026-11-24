#!/usr/bin/env python3
"""Verify retained artifact bytes against a versioned tau provenance envelope.

This is an offline integrity check only. It does not resolve Git commits, prove
that a run used the declared files, attest an execution environment, or assess
scientific independence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = 1
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_GIT_OBJECT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _artifact_error(entry: Any, label: str, root: Path) -> tuple[str | None, str | None]:
    """Return (normalized relative path, error); never follows paths outside root."""
    if not isinstance(entry, dict):
        return None, f"{label} must be an object"
    path_value = entry.get("path")
    digest = entry.get("sha256")
    if not _nonempty_string(path_value):
        return None, f"{label}.path must be a non-empty relative path"
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        return None, f"{label}.sha256 must be a 64-character lowercase SHA-256"
    posix_path = PurePosixPath(path_value)
    if posix_path.is_absolute() or any(part in ("", ".", "..") for part in posix_path.parts):
        return None, f"{label}.path must be a normalized relative path without dot segments"
    if "\\" in path_value:
        return None, f"{label}.path must use forward-slash separators"
    candidate = root.joinpath(*posix_path.parts)
    current = root
    for part in posix_path.parts:
        current = current / part
        if current.is_symlink():
            return None, f"{label}.path must not traverse symlinks"
    try:
        resolved = candidate.resolve(strict=True)
    except OSError:
        return None, f"{label}.path does not exist"
    try:
        resolved.relative_to(root)
    except ValueError:
        return None, f"{label}.path resolves outside the artifact root"
    if not resolved.is_file():
        return None, f"{label}.path must identify a regular file"
    actual = hashlib.sha256(resolved.read_bytes()).hexdigest()
    if actual != digest:
        return None, f"{label}.sha256 does not match retained file bytes"
    return posix_path.as_posix(), None


def verify_envelope(envelope: Any, artifact_root: Path) -> dict[str, Any]:
    """Validate envelope shape and recompute every declared artifact digest."""
    errors: list[str] = []
    if not isinstance(envelope, dict):
        return {
            "schema_version": SCHEMA_VERSION,
            "verification_status": "invalid",
            "errors": ["envelope must be a JSON object"],
            "repository_commit_resolution": "not_performed",
            "execution_attestation": "not_performed",
            "scientific_adjudication": "not_performed",
        }
    if envelope.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")

    repository = envelope.get("repository")
    if not isinstance(repository, dict):
        errors.append("repository must be an object")
        repository = {}
    if not _nonempty_string(repository.get("url")):
        errors.append("repository.url must be a non-empty canonical repository URL")
    commit = repository.get("commit")
    if not isinstance(commit, str) or not _GIT_OBJECT_ID.fullmatch(commit):
        errors.append("repository.commit must be a full lowercase 40- or 64-character Git object ID")
    if repository.get("working_tree_clean") is not True:
        errors.append("repository.working_tree_clean must be true")

    evaluator = envelope.get("evaluator")
    if not isinstance(evaluator, dict):
        errors.append("evaluator must be an object")
        evaluator = {}
    if not _nonempty_string(evaluator.get("version")):
        errors.append("evaluator.version must be a non-empty string")
    evaluator_files = evaluator.get("source_files")
    if not isinstance(evaluator_files, list) or not evaluator_files:
        errors.append("evaluator.source_files must be a non-empty list")

    execution = envelope.get("execution")
    if not isinstance(execution, dict):
        errors.append("execution must be an object")
        execution = {}
    if not _nonempty_string(execution.get("python_version")):
        errors.append("execution.python_version must be a non-empty string")
    if not _nonempty_string(execution.get("command")):
        errors.append("execution.command must be a non-empty string")
    arguments = execution.get("arguments")
    if not isinstance(arguments, list) or any(not isinstance(arg, str) for arg in arguments):
        errors.append("execution.arguments must be a list of strings")
    dependency_lock = execution.get("dependency_lock")
    if not isinstance(dependency_lock, dict):
        errors.append("execution.dependency_lock must be an artifact object")

    inputs = envelope.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        errors.append("inputs must be a non-empty list")
    output = envelope.get("output")
    if not isinstance(output, dict):
        errors.append("output must be an artifact object")

    root = artifact_root.resolve()
    if not root.is_dir():
        errors.append("artifact root must be an existing directory")
    verified_paths: set[str] = set()
    entries: list[tuple[str, Any]] = []
    if isinstance(evaluator_files, list):
        entries.extend((f"evaluator.source_files[{i}]", item) for i, item in enumerate(evaluator_files))
    if isinstance(dependency_lock, dict):
        entries.append(("execution.dependency_lock", dependency_lock))
    if isinstance(inputs, list):
        entries.extend((f"inputs[{i}]", item) for i, item in enumerate(inputs))
    if isinstance(output, dict):
        entries.append(("output", output))

    if root.is_dir():
        for label, entry in entries:
            relative, error = _artifact_error(entry, label, root)
            if error:
                errors.append(error)
            elif relative in verified_paths:
                errors.append(f"artifact path is declared more than once: {relative}")
            else:
                verified_paths.add(relative)

    return {
        "schema_version": SCHEMA_VERSION,
        "verification_status": "artifact_digests_verified" if not errors else "invalid",
        "verified_artifact_count": len(verified_paths) if not errors else 0,
        "verified_artifact_paths": sorted(verified_paths) if not errors else [],
        "errors": errors,
        "repository_commit_resolution": "not_performed",
        "execution_attestation": "not_performed",
        "scientific_adjudication": "not_performed",
        "limitations": [
            "The commit ID is syntax-checked but not resolved against the declared repository.",
            "A clean-working-tree value is a declaration, not independently verified here.",
            "Matching artifact bytes do not prove those bytes were used in the reported execution.",
            "A digest cannot establish mathematical family independence or human-review correctness.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--envelope", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        envelope = json.loads(args.envelope.read_text(encoding="utf-8"))
        report = verify_envelope(envelope, args.artifact_root)
        rendered = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    return 0 if report["verification_status"] == "artifact_digests_verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
