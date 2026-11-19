"""Regression test for the V60 production-result handoff binding."""


def test_v60_hybrid_system_exposes_native_result_builder():
    from hypatiax.tools.symbolic.hybrid_system_v60 import build_native_v60_result

    assert callable(build_native_v60_result)
