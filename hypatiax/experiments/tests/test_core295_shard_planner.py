import unittest
from collections import Counter

from hypatiax.experiments.benchmarks.core295_catalogue import (
    DOMAINS,
    plan_domain_balanced_shards,
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

    def test_invalid_shard_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "n_shards"):
            plan_domain_balanced_shards([], 0)


if __name__ == "__main__":
    unittest.main()
