import hashlib

import pytest
from pathlib import Path

from scripts.verify_tau_provenance_envelope import verify_envelope


def _write(root: Path, relative: str, data: bytes) -> dict[str, str]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"path": relative, "sha256": hashlib.sha256(data).hexdigest()}


def _fixture(tmp_path):
    root = tmp_path / "artifacts"
    root.mkdir()
    source = _write(root, "scripts/evaluator.py", b"print('evaluator')\n")
    lock = _write(root, "requirements.lock", b"package==1.0\n")
    manifest = _write(root, "inputs/frozen-manifest.json", b'{"frozen":true}\n')
    outcomes = _write(root, "outputs/report.json", b'{"result":"frozen"}\n')
    envelope = {
        "schema_version": 1,
        "repository": {
            "url": "https://github.com/example/project",
            "commit": "a" * 40,
            "working_tree_clean": True,
        },
        "evaluator": {"version": "tau-evaluator-v1", "source_files": [source]},
        "execution": {
            "python_version": "3.12.0",
            "dependency_lock": lock,
            "command": "python scripts/evaluate.py",
            "arguments": ["--input", "manifest.json"],
        },
        "inputs": [manifest],
        "output": outcomes,
    }
    return root, envelope


def test_valid_envelope_recomputes_all_artifact_digests(tmp_path):
    root, envelope = _fixture(tmp_path)
    report = verify_envelope(envelope, root)
    assert report["verification_status"] == "artifact_digests_verified"
    assert report["verified_artifact_count"] == 4
    assert report["repository_commit_resolution"] == "not_performed"
    assert report["execution_attestation"] == "not_performed"
    assert report["scientific_adjudication"] == "not_performed"


def test_tampered_artifact_bytes_are_rejected(tmp_path):
    root, envelope = _fixture(tmp_path)
    (root / "inputs/frozen-manifest.json").write_text('{"frozen":false}\n')
    report = verify_envelope(envelope, root)
    assert report["verification_status"] == "invalid"
    assert any("does not match retained file bytes" in error for error in report["errors"])


def test_missing_artifact_is_rejected(tmp_path):
    root, envelope = _fixture(tmp_path)
    (root / "requirements.lock").unlink()
    report = verify_envelope(envelope, root)
    assert report["verification_status"] == "invalid"
    assert any("execution.dependency_lock.path does not exist" in error for error in report["errors"])


def test_path_traversal_is_rejected(tmp_path):
    root, envelope = _fixture(tmp_path)
    envelope["inputs"][0]["path"] = "../outside.json"
    report = verify_envelope(envelope, root)
    assert report["verification_status"] == "invalid"
    assert any("normalized relative path" in error for error in report["errors"])


def test_duplicate_artifact_path_is_rejected(tmp_path):
    root, envelope = _fixture(tmp_path)
    envelope["inputs"].append(dict(envelope["inputs"][0]))
    report = verify_envelope(envelope, root)
    assert report["verification_status"] == "invalid"
    assert any("declared more than once" in error for error in report["errors"])


def test_symlink_artifact_is_rejected(tmp_path):
    root, envelope = _fixture(tmp_path)
    target = root / "inputs/frozen-manifest.json"
    link = root / "inputs/linked-manifest.json"
    link.symlink_to(target)
    envelope["inputs"] = [{
        "path": "inputs/linked-manifest.json",
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    }]
    report = verify_envelope(envelope, root)
    assert report["verification_status"] == "invalid"
    assert any("must not traverse symlinks" in error for error in report["errors"])


def test_well_formed_but_unresolved_commit_is_not_claimed_verified(tmp_path):
    root, envelope = _fixture(tmp_path)
    envelope["repository"]["commit"] = "f" * 40
    report = verify_envelope(envelope, root)
    assert report["verification_status"] == "artifact_digests_verified"
    assert report["repository_commit_resolution"] == "not_performed"


def test_non_object_envelope_is_rejected(tmp_path):
    root, _ = _fixture(tmp_path)
    report = verify_envelope(["not", "an", "object"], root)
    assert report["verification_status"] == "invalid"
    assert report["errors"] == ["envelope must be a JSON object"]


@pytest.mark.parametrize(
    "path_value",
    [
        "inputs//manifest.json",
        "inputs/./manifest.json",
        "inputs/../manifest.json",
        "/inputs/manifest.json",
        "inputs/manifest.json/",
        "C:/outside.json",
        "inputs/bad\x00name.json",
        r"inputs\\manifest.json",
    ],
)
def test_noncanonical_artifact_paths_are_rejected(tmp_path, path_value):
    root, envelope = _fixture(tmp_path)
    envelope["inputs"][0]["path"] = path_value
    report = verify_envelope(envelope, root)
    assert report["verification_status"] == "invalid"
    assert any("path" in error and ("normalized" in error or "portable" in error or "canonical" in error)
               for error in report["errors"])


@pytest.mark.parametrize(
    "repository_url",
    [
        "http://github.com/owner/repository",
        "https://github.com/owner",
        "https://github.com/owner/repository/",
        "https://github.com/owner/repository.git",
        "https://github.com.evil.example/owner/repository",
        "https://user@github.com/owner/repository",
        "https://github.com/owner/repository?redirect=elsewhere",
        "https://github.com/owner/repository#fragment",
        "https://github.com/owner/repo%2Fother",
        "https://github.com/-invalid/repository",
        "https://github.com/owner/repository\\n",
        "https://github.com/owner/repo\\tname",
    ],
)
def test_noncanonical_repository_urls_are_rejected(tmp_path, repository_url):
    root, envelope = _fixture(tmp_path)
    envelope["repository"]["url"] = repository_url
    report = verify_envelope(envelope, root)
    assert report["verification_status"] == "invalid"
    assert any("repository.url must be a canonical" in error for error in report["errors"])


def test_canonical_github_repository_url_is_accepted(tmp_path):
    root, envelope = _fixture(tmp_path)
    envelope["repository"]["url"] = "https://github.com/valid-owner/repository_name.v2"
    report = verify_envelope(envelope, root)
    assert report["verification_status"] == "artifact_digests_verified"
