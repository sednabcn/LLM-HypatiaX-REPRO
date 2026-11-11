import unittest
from collections import Counter

from hypatiax.experiments.benchmarks.core295_catalogue import (
    DOMAINS,
    equations_from_manifest,
    plan_domain_balanced_shards,
    smoke_check_equations,
    validate_shard_plan,
)


def synthetic_entries():
    return [
        {
            "equation_id": f"CORE295-{domain.upper().replace(' ', '-')}-{index:03d}",
            "domain": domain,
            "status": "accepted",
        }
        for domain in DOMAINS
        for index in range(59)
    ]


class TestCore295ShardPlanner(unittest.TestCase):
    def test_295_tasks_are_assigned_once_and_balanced(self):
        entries = synthetic_entries()
        shards = plan_domain_balanced_shards(entries, n_shards=100)
        validate_shard_plan(entries, shards)
        sizes = [len(shard) for shard in shards]
        self.assertEqual(sum(sizes), 295)
        self.assertLessEqual(max(sizes) - min(sizes), 1)
        self.assertEqual(set(sizes), {2, 3})

    def test_all_domains_are_present_in_allocation(self):
        entries = synthetic_entries()
        shards = plan_domain_balanced_shards(entries, n_shards=100)
        assigned = Counter(entry["domain"] for shard in shards for entry in shard)
        self.assertEqual(assigned, Counter({domain: 59 for domain in DOMAINS}))

    def test_result_is_deterministic(self):
        entries = synthetic_entries()
        first = [[item["equation_id"] for item in shard]
                 for shard in plan_domain_balanced_shards(entries, 100)]
        second = [[item["equation_id"] for item in shard]
                  for shard in plan_domain_balanced_shards(entries, 100)]
        self.assertEqual(first, second)

    def test_duplicate_ids_are_rejected(self):
        entries = synthetic_entries()
        entries[1] = dict(entries[1], equation_id=entries[0]["equation_id"])
        with self.assertRaisesRegex(ValueError, "duplicate equation_id"):
            plan_domain_balanced_shards(entries, 100)

    def test_symbolic_manifest_record_adapts_to_core15_api(self):
        record = {
            "equation_id": "CORE295-CHEM-TEST-001",
            "name": "Exponential Decay Candidate",
            "domain": "Chemistry",
            "subdomain": "kinetics",
            "formula": "a*exp(-k*t)",
            "canonical_expression": "a*exp(-k*t)",
            "variables": {"a": {"meaning": "initial amount"}, "k": {"meaning": "rate"}, "t": {"meaning": "time"}},
            "input_ranges": {
                "a": {"train": [1.0, 2.0], "extrapolation": [2.0, 3.0]},
                "k": {"train": [0.1, 0.5], "extrapolation": [0.5, 1.0]},
                "t": {"train": [0.0, 2.0], "extrapolation": [2.0, 4.0]},
            },
            "source_family_id": "chem-kinetics-test-family",
            "source_ids": ["CHEM-OPENSTAX-2E"],
            "status": "accepted",
        }
        data = {"catalogue_id": "core295-option2", "entries": [record]}
        equations = equations_from_manifest(data, require_complete=False)
        self.assertEqual(equations[0]["vars"], ["a", "k", "t"])
        self.assertEqual(equations[0]["domain"], "Chemistry")
        smoke_check_equations(equations)

    def test_undeclared_symbol_is_rejected(self):
        record = {
            "equation_id": "CORE295-CHEM-TEST-002",
            "name": "Bad Candidate",
            "domain": "Chemistry",
            "subdomain": "kinetics",
            "formula": "a*z",
            "canonical_expression": "a*z",
            "variables": {"a": {"meaning": "amount"}},
            "input_ranges": {"a": {"train": [1.0, 2.0], "extrapolation": [2.0, 3.0]}},
            "source_family_id": "chem-family",
            "source_ids": ["CHEM-OPENSTAX-2E"],
            "status": "accepted",
        }
        with self.assertRaisesRegex(ValueError, "undeclared symbols"):
            equations_from_manifest(
                {"catalogue_id": "core295-option2", "entries": [record]},
                require_complete=False,
            )

    def test_arbitrary_python_calls_are_rejected(self):
        record = {
            "equation_id": "CORE295-CHEM-TEST-003",
            "name": "Unsafe Candidate",
            "domain": "Chemistry",
            "subdomain": "kinetics",
            "formula": "unsafe",
            "canonical_expression": "__import__('os').system('echo unsafe')",
            "variables": {"t": {"meaning": "time"}},
            "input_ranges": {"t": {"train": [0.0, 1.0], "extrapolation": [1.0, 2.0]}},
            "source_family_id": "chem-family",
            "source_ids": ["CHEM-OPENSTAX-2E"],
            "status": "accepted",
        }
        with self.assertRaisesRegex(ValueError, "invalid canonical_expression"):
            equations_from_manifest(
                {"catalogue_id": "core295-option2", "entries": [record]},
                require_complete=False,
            )

    def test_invalid_shard_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "n_shards"):
            plan_domain_balanced_shards([], 0)


if __name__ == "__main__":
    unittest.main()
