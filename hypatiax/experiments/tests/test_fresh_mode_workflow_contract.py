"""No-API contract tests for the original workflow's guarded fresh mode.

Fresh mode is intentionally limited to exp1-provenance until the remaining
fresh protocol stages are mapped to the original planner/PCA job architecture.
These tests inspect workflow policy; they never dispatch jobs or call APIs.
"""
from pathlib import Path
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
        self.assertIn("RESULTS_DIR:       ${{ env.OUT_BASE }}", self.text)
        self.assertNotIn("github.workspace }}/${{ env.OUT_BASE }}", self.text)

    def test_all_checkpoint_cache_actions_are_disabled_in_fresh_mode(self):
        lines = self.text.splitlines()
        cache_actions = 0
        for index, line in enumerate(lines):
            if "uses: actions/cache/restore@" in line or "uses: actions/cache/save@" in line:
                cache_actions += 1
                preceding = lines[max(0, index - 3):index]
                step_if = next(
                    (item.strip() for item in reversed(preceding) if item.strip().startswith("if:")),
                    None,
                )
                self.assertIsNotNone(step_if, line)
                self.assertIn("fresh_mode", step_if, line)
        self.assertEqual(cache_actions, 4)

    def test_fresh_mode_never_seeds_or_resumes_checkpoints(self):
        self.assertIn("github.event.inputs.fresh_mode != 'true' }}", self.text)
        resume_lines = [line for line in self.text.splitlines() if "RESUME:" in line]
        self.assertTrue(any("fresh_mode == 'true'" in line and "'false'" in line for line in resume_lines))

    def test_result_commits_and_repo_verification_are_skipped(self):
        expected = [
            "Commit and push shard results to repo\n        if: ${{ success() && github.event.inputs.fresh_mode != 'true' }}",
            "Verify results committed to repo\n        if: ${{ success() && github.event.inputs.fresh_mode != 'true' }}",
        ]
        for step in expected:
            self.assertIn(step, self.text)
        baseline = self.text.split("Commit and push corrected baseline", 1)[1]
        self.assertIn("github.event.inputs.fresh_mode != 'true'", baseline)

    def test_seed_sharding_and_artifact_upload_are_preserved(self):
        self.assertIn('\"exp1-provenance\":    5', self.text)
        self.assertIn('name: results-${{ github.event.inputs.experiment }}-shard', self.text)
        self.assertIn('retention-days: ${{ github.event.inputs.experiment == \'exp1-provenance\' && 90 || 30 }}', self.text)
        self.assertIn("exp1-provenance-aggregate-run", self.text)


if __name__ == "__main__":
    unittest.main()
