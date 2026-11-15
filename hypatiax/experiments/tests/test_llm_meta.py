from hypatiax.core.llm_meta import llm_meta


def test_reads_engine_llm_info():
    res = {"llm_info": {"llm_time": 11.5, "llm_best_expression": "a*b", "llm_confidence": 0.8}}
    assert llm_meta(res) == {"llm_time_s": 11.5, "llm_expression": "a*b", "llm_confidence": 0.8}


def test_missing_or_malformed_info_falls_back():
    for res in ({}, None, {"llm_info": None}, {"llm_info": "x"}):
        assert llm_meta(res) == {"llm_time_s": 0.0, "llm_expression": None, "llm_confidence": None}


def test_bad_values_are_not_propagated():
    res = {"llm_info": {"llm_time": float("nan"), "llm_best_expression": "", "llm_confidence": "high"}}
    assert llm_meta(res) == {"llm_time_s": 0.0, "llm_expression": None, "llm_confidence": None}


def test_boolean_values_are_not_numeric_metadata():
    res = {"llm_info": {"llm_time": True, "llm_confidence": False}}
    assert llm_meta(res) == {"llm_time_s": 0.0, "llm_expression": None, "llm_confidence": None}
