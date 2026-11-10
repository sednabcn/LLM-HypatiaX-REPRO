"""No-API contract tests for the original workflow's guarded fresh mode.

Fresh mode is intentionally limited to exp1-provenance until the remaining
fresh protocol stages are mapped to the original planner/PCA job architecture.
These tests inspect workflow policy; they never dispatch jobs or call APIs.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "ci_runner_repro.yml"


class FreshModeWorkflowContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_fresh_mode_is_opt_in_and_limited_to_provenance_run(self):
        self.assertIn("      fresh_mode:", self.text)
        self.assertIn('        default: "false"', self.text)
        self.assertIn('if [[ "$EXP" != "exp1-provenance" ]]', self.text)
        self.assertIn('if [[ "$ID" != "exp1-provenance" ]]', self.text)

    def test_output_root_is_run_and_attempt_isolated_outside_checkout(self):
        self.assertIn("hypatiax-fresh-{1}-attempt-{2}", self.text)
        self.assertIn("github.run_id", self.text)
        self.assertIn("github.run_attempt", self.text)
        self.assertIn("Assert fresh output root is unused", self.text)
        self.assertIn('if [[ -e "${OUT_BASE}" ]]; then', self.text)

    def test_all_checkpoint_cache_actions_are_disabled_in_fresh_mode(self):
        for line in self.text.splitlines():
            if "uses: actions/cache/restore@" in line or "uses: actions/cache/save@" in line:
                # The corresponding step-level if must be guarded. Check the
                # nearest preceding if in the workflow text.
                prefix = self.text[: self.text.index(line)]
                preceding_if = re.findall(r"^\s+if: (.+)$", prefix, re.MULTILINE)
                self.assertTrue(preceding_if, line)
                self.assertIn("fresh_mode", preceding_if[-1], line)
        self.assertIn("github.event.inputs.fresh_mode != 'true'", self.text)

    def test_fresh_mode_never_seeds_or_resumes_checkpoints(self):
        self.assertIn("github.event.inputs.fresh_mode != 'true' }}", self.text)
        resume_lines = [line for line in self.text.splitlines() if "RESUME:" in line]
        self.assertTrue(any("fresh_mode == 'true'" in line and "'false'" in line for line in resume_lines))

    def test_result_commits_and_repo_verification_are_skipped(self):
        expected = [
            "Commit and push shard results to repo",
            "Verify results committed to repo",
            "Commit and push corrected baseline",
        ]
        for step in expected:
            self.assertIn(step, self.text)
        self.assertGreaterEqual(
            self.text.count("github.event.inputs.fresh_mode != 'true'"),
            5,
        )

    def test_seed_sharding_and_artifact_upload_are_preserved(self):
        self.assertIn('exp1-provenance:    5', self.text)
        self.assertIn('name: results-${{ github.event.inputs.experiment }}-shard', self.text)
        self.assertIn('retention-days: ${{ github.event.inputs.experiment == \'exp1-provenance\' && 90 || 30 }}', self.text)
        self.assertIn("exp1-provenance-aggregate-run", self.text)


if __name__ == "__main__":
    unittest.main()
