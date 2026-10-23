"""Shared pytest setup for hypatiax/experiments/tests.

test_recovery_evaluator.py deliberately fails unless RECOVERY_EVAL names the
evaluator under test (module:function), so a gate that cannot run cannot pass.
Default it to the repo's canonical evaluator; CI or a developer can still
override it by exporting RECOVERY_EVAL before running pytest.
"""
import os

os.environ.setdefault("RECOVERY_EVAL", "hypatiax.core.recovery_eval:recovery_r2")
