import copy
import json
import unittest
from pathlib import Path

from scripts.validate_core295_catalogue import DOMAINS, validate

MANIFEST = Path(__file__).resolve().parents[2] / "config" / "core295_catalogue.json"


class TestCore295Catalogue(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_draft_manifest_is_structurally_valid(self):
        self.assertEqual(validate(self.data), [])

    def test_wrong_target_count_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["target_equation_count"] = 300
        self.assertTrue(any("target_equation_count" in e for e in validate(data)))

    def test_wrong_domain_order_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["domains"] = list(reversed(DOMAINS))
        self.assertTrue(any("domains must be exactly" in e for e in validate(data)))

    def test_unknown_source_reference_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["entries"] = [{
            "equation_id": "CORE295-CHEM-0001",
            "name": "Candidate",
            "domain": "Chemistry",
            "subdomain": "kinetics",
            "formula": "y = exp(-k*t)",
            "canonical_expression": "exp(-k*t)",
            "structural_fingerprint": "a" * 64,
            "source_ids": ["NO-SUCH-SOURCE"],
            "source_family_id": "family-1",
            "status": "proposed",
            "assumptions": "test",
            "variables": {"t": "time"},
            "validity": "t >= 0",
            "input_ranges": {"t": [0, 1]},
            "generator": {"version": "draft"}
        }]
        self.assertTrue(any("unknown source_id" in e for e in validate(data)))

    def test_duplicate_fingerprints_are_rejected(self):
        data = copy.deepcopy(self.data)
        base = {
            "name": "Candidate",
            "domain": "Chemistry",
            "subdomain": "kinetics",
            "formula": "y = exp(-k*t)",
            "canonical_expression": "exp(-k*t)",
            "structural_fingerprint": "b" * 64,
            "source_ids": ["CHEM-OPENSTAX-2E"],
            "source_family_id": "family-1",
            "status": "proposed",
            "assumptions": "test",
            "variables": {"t": "time"},
            "validity": "t >= 0",
            "input_ranges": {"t": [0, 1]},
            "generator": {"version": "draft"}
        }
        data["entries"] = [
            dict(base, equation_id="CORE295-CHEM-0001"),
            dict(base, equation_id="CORE295-CHEM-0002")
        ]
        self.assertTrue(any("structural fingerprint collision" in e for e in validate(data)))

    def test_draft_cannot_pass_readiness(self):
        errors = validate(self.data, require_ready=True)
        self.assertTrue(any("status must be 'ready'" in e for e in errors))
        self.assertTrue(any("exactly 59 required" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
