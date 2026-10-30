"""
hypatia_llm_hook.py -- enforce salt / blind / call-count on the Hypatia arm's LLM path.

The hypatia arm does NOT go through hypatia.get_llm_prior. It uses
hypatiax.tools.symbolic.symbolic_engine (SymbolicEngineWithLLM -> generate_hypotheses
-> _build_prompt -> _call_llm). This hook patches that class for one (condition, seed):

  salt   : appended (hashed) to caller_id, which _build_prompt embeds as "# caller: ..."
           in the prompt text, so any prompt-keyed cache gives one entry per
           condition+seed.
  blind  : forces the existing HYPATIAX_DISABLE_PROMPT_HINTS guard on (description is
           replaced by "(withheld - ...)") AND replaces the prompt's "Domain:" with
           "unspecified". The engine itself still receives the real domain.
  count  : every generate_hypotheses call increments log["calls"]; the first prompts
           are kept in log["prompts"] so the neutral prompt can be audited.

Used via:  ablation_conditions.py run --hook hypatia_llm_hook:hybrid_llm_condition
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib
import inspect

ENGINE_MODULE = "hypatiax.tools.symbolic.symbolic_engine"
FLAGS_MODULE = "hypatiax.core.flags"
HINT_FLAG = "HYPATIAX_DISABLE_PROMPT_HINTS"


@contextlib.contextmanager
def hybrid_llm_condition(salt, blind, log, module=ENGINE_MODULE):
    mod = importlib.import_module(module)
    classes = [c for c in vars(mod).values()
               if inspect.isclass(c) and {"generate_hypotheses", "_build_prompt", "_call_llm"} <= set(vars(c))]
    if not classes:
        raise RuntimeError(f"no class with generate_hypotheses/_build_prompt/_call_llm in {module}")
    tag = "salt:" + hashlib.sha1(salt.encode()).hexdigest()[:10]
    flags = importlib.import_module(FLAGS_MODULE)
    orig_flag = flags.flag_on
    saved = []

    def flag_on(name, *a, **k):
        if blind and name == HINT_FLAG:
            return True
        return orig_flag(name, *a, **k)

    def make(cls):
        og, ob, oc = cls.generate_hypotheses, cls._build_prompt, cls._call_llm
        sg, sb = inspect.signature(og), inspect.signature(ob)

        def gen(self, *a, **k):
            b = sg.bind(self, *a, **k)
            b.apply_defaults()
            cid = b.arguments.get("caller_id", "") or ""
            b.arguments["caller_id"] = f"{cid}|{tag}" if cid else tag
            log["calls"] += 1
            return og(*b.args, **b.kwargs)

        def bp(self, *a, **k):
            b = sb.bind(self, *a, **k)
            if blind:
                b.arguments["domain"] = "unspecified"
            return ob(*b.args, **b.kwargs)

        def call(self, prompt):
            if len(log.setdefault("prompts", [])) < 3:
                log["prompts"].append(prompt)
            return oc(self, prompt)

        saved.append((cls, og, ob, oc))
        cls.generate_hypotheses, cls._build_prompt, cls._call_llm = gen, bp, call

    try:
        flags.flag_on = flag_on
        for c in classes:
            make(c)
        yield
    finally:
        flags.flag_on = orig_flag
        for cls, og, ob, oc in saved:
            cls.generate_hypotheses, cls._build_prompt, cls._call_llm = og, ob, oc
