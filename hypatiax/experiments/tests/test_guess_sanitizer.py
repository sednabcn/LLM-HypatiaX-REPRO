try:  # inside the repo package, else a flat copy next to this file
    from hypatiax.tools.symbolic import guess_sanitizer as G
except ImportError:
    import guess_sanitizer as G
B, U, V = ["+", "-", "*", "/"], ["sqrt"], ["x0", "x1"]

def t(g, b=B, u=U):
    return G.sanitize_guesses([g], b, u, V)

def test_transcript_case():
    kept, dropped = G.sanitize_guesses(["-x0**2 + 0.16", "sign(x0)", "x0**0.75"], B, U, V)
    assert kept == ["(0.16 - (x0 * x0))"]
    assert dict(dropped) == {"sign(x0)": "unsupported_operator:sign", "x0**0.75": "needs_pow"}

def test_pow_added_when_available():
    assert t("x0**0.75", B + ["^"])[0] == ["(x0 ^ 0.75)"]
    assert t("x0^x1", B + ["pow"])[0] == ["pow(x0, x1)"]

def test_unary_minus():
    assert t("-x0")[0] == ["(0 - x0)"]
    assert t("x0 - -x1")[0] == ["(x0 + x1)"]

def test_unary_fn_and_unknowns():
    assert t("sqrt(x0)")[0] == ["sqrt(x0)"]
    assert t("exp(x0)")[1] == [("exp(x0)", "unsupported_operator:exp")]
    assert t("y + 1")[1][0][1] == "unknown_name:y"
    assert t("x0 +")[1][0][1] == "unparseable"

def test_missing_binary_op():
    assert t("x0 * x1", ["+", "-"])[1][0][1] == "unsupported_operator:*"

def test_duplicate_and_audit():
    G.reset_audit()
    G.record_llm_response("raw response A")
    kept, dropped = G.sanitize_guesses(["x0*x1", "x0 * x1", "sign(x0)"], B, U, V)
    G.record_audit(["x0*x1", "x0 * x1", "sign(x0)"], kept, dropped)
    r = G.drain_audit()
    assert (r["guesses_requested"], r["guesses_used"], r["guesses_dropped"]) == (3, 1, 2)
    assert r["guess_fit_fallback"] is False and r["llm_sample_sha256"]
    assert G.drain_audit()["guesses_requested"] == 0


def test_response_hash_independent_of_guesses():
    # accepted answer, no guesses requested: the sample hash must still be set
    G.reset_audit()
    G.record_llm_response("raw response A")
    a = G.drain_audit()
    assert a["guesses_requested"] == 0 and a["llm_sample_sha256"]
    # same response, now with a seeded fit: same sample hash
    G.reset_audit()
    G.record_llm_response("raw response A")
    G.record_llm_response("raw response A")          # repeated call (attempt 2): still one sample
    G.record_audit(["x0*x1"], ["(x0 * x1)"], [])
    b = G.drain_audit()
    assert b["llm_sample_sha256"] == a["llm_sample_sha256"]
    assert b["guess_set_sha256"] and a["guess_set_sha256"] is None
    # different response -> different sample hash
    G.reset_audit()
    G.record_llm_response("raw response B")
    assert G.drain_audit()["llm_sample_sha256"] != a["llm_sample_sha256"]
    # no LLM response at all
    G.reset_audit()
    assert G.drain_audit()["llm_sample_sha256"] is None
