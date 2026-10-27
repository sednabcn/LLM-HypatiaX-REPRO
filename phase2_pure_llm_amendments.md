# Phase 2 Pure LLM run: amendments log

## Amendment A1 (2026-10-27)
- D3 settled: prompt inputs are domain, variable names, data-pattern statistics and constants block; equation name withheld.
- D5 decided: Pure LLM arm returns 3 candidates (matching HDS) and the winner is chosen on training R2 only. If the runner cannot do this, the difference must be labelled in the report.
- Config: temperature=0.3, max_tokens=2000, max_calls_per_case=1 (CONFIRM max_calls_per_case against the HDS code).
- OPEN (blocks any Pure LLM run): PureLLMBaseline sends no temperature and uses max_tokens=4000, while the HDS stage reads 0.3 / 2000. Confirm what is actually sent and align or label it.
- OPEN: PureLLMBaseline prompt not yet compared with the HDS prompt; prompt_template_sha256 not frozen.
- OPEN: D6 (see spec) not recorded here; settle it in the spec itself.

## Amendment A2 (2026-10-27)
- test_error_row_is_not_counted_as_llm_call_and_keeps_hint_status updated to expect bypass_kind "live". The prompt is a single equation-agnostic template (hints deleted, not gated) with a leak-marker guard. The test also failed at phase1-closed (9d56d8c), so it was stale then, not a regression.
- VERIFIED: the 90 p2/ rows trace to CI result files committed 2026-10-26 (runs 40301286024, 40379400415), after clean-run commit ed5dd78 (2026-10-23). HDS rows: bypass_kind "none", llm_called True for 45/45; PySR rows: llm_called False. TO CONFIRM: CI head commit of each run; engine_version "5.4" maps to the v50_2 label.
- FINDING: PureLLMBaseline strips _x_stats/_y_stats and its prompt builder has no slot for data statistics; the HDS clean prompt sends data-pattern statistics. test_prompt_parity.py compares the baseline with the nn hybrid fallback, not HDS v50_2, and does not cover statistics. DECISION REQUIRED: (a) add an identical statistics block to the Pure LLM prompt (reverses a Phase 1 guard; update parity test item 4), or (b) run Pure LLM on description + variables + constants only and declare that HDS sees more information.
- OPEN: PureLLMBaseline results produced before ed5dd78 may have used the legacy hint path; none are in p2/. Keep them on the quarantine list.
