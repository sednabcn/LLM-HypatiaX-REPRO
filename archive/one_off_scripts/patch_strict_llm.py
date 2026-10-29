import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()

def sub(old, new):
    global s
    assert s.count(old) == 1, f"expected exactly one match for:\n{old[:120]}"
    s = s.replace(old, new)

# 1. track last call state on the engine
sub("""    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
""", """    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self.last_call_attempted = False
        self.last_error = None
""")

# 2. split API failure from parse failure; raise API failures under strict
sub("""        try:
            response = self._call_llm(prompt)
            hypotheses = self._parse_response(response)
            return hypotheses
        except Exception as e:
            print(f"⚠️  LLM generation failed: {e}")
            return []
""", """        self.last_call_attempted = True
        self.last_error = None
        try:
            response = self._call_llm(prompt)
        except Exception as e:
            # API / connection / timeout failure: never let it look like a
            # model that simply returned nothing.
            self.last_error = f"{type(e).__name__}: {e}"
            print(f"⚠️  LLM generation failed: {self.last_error}")
            if os.environ.get("HYPATIAX_STRICT") == "1":
                raise
            return []
        hypotheses = self._parse_response(response)
        if not hypotheses:
            self.last_error = "parse_failed_or_empty_response"
        return hypotheses
""")

# 3. record the attempt in the fallback row
sub("""            result["llm_mode"] = "hybrid_llm_failed"
            return result
""", """            result["llm_mode"] = "hybrid_llm_failed"
            result["llm_called"] = bool(getattr(self.llm_engine, "last_call_attempted", False))
            result["llm_error"] = getattr(self.llm_engine, "last_error", None)
            return result
""")
open(p, "w", encoding="utf-8").write(s)
print("patched", p)
