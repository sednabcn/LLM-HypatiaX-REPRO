# Phase 2 Pure LLM run: amendments log

## Amendment A1 (2026-10-27)
- D3 settled: prompt inputs are domain, variable names, data-pattern statistics and constants block; equation name withheld.
- D5 decided: Pure LLM arm returns 3 candidates (matching HDS) and the winner is chosen on training R2 only. If the runner cannot do this, the difference must be labelled in the report.
- Config: temperature=0.3, max_tokens=2000, max_calls_per_case=1 (CONFIRM max_calls_per_case against the HDS code).
- OPEN (blocks any Pure LLM run): PureLLMBaseline sends no temperature and uses max_tokens=4000, while the HDS stage reads 0.3 / 2000. Confirm what is actually sent and align or label it.
- OPEN: PureLLMBaseline prompt not yet compared with the HDS prompt; prompt_template_sha256 not frozen.
- OPEN: D6 (see spec) not recorded here; settle it in the spec itself.
