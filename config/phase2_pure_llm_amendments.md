# Phase 2 prompt amendment — matched HDS inputs

**Decision date:** 20 November 2026  
**Status:** Approved design; implementation and offline verification required before any API call.

## Decision

The primary Pure-LLM arm will receive the same *information classes* as the HDS LLM stage, while remaining a separate generation system:

- domain;
- variable names;
- training-split pattern statistics computed only from `X_train` and `y_train`;
- the same fixed, rounded physical-constants block used by HDS.

The Pure-LLM prompt must not receive the equation name, equation description, target formula, formula hint, or any statistics computed from validation, near/medium/far extrapolation, or test data. The neutral task wording must not name the benchmark equation.

## Generation and selection retained

- Three independent Pure-LLM API calls per (equation, seed).
- Each call returns one formula using the Pure-LLM parser/evaluator contract.
- Candidate selection uses training R² only. No validation or extrapolation score may influence selection.
- HDS's three candidates in one request followed by PySR refinement are not equivalent to three independent Pure-LLM requests. This request-shape and refinement difference must be stated in all Phase 2 reporting; this amendment matches prompt information, not the complete algorithms.
- Temperature remains 0.25 and max_tokens remains 2000, subject to request-capture verification against HDS.

## Implementation contract

1. Use the exact training arrays used by the Phase 2 case generator.
2. Reuse the HDS pattern-summary implementation, not a newly invented summary. Add a regression test that compares the Pure-LLM pattern payload to the HDS payload for the same arrays.
3. Reuse the exact rounded constants block from the HDS prompt. Do not substitute the more precise CODATA constants.
4. Render both prompts offline for a fixed fixture and verify the allowed input values are identical.
5. Verify that the Pure-LLM prompt contains no equation name, description, formula hint, or test/extrapolation-derived value.
6. Verify the prompt is stable across the three calls for a case and record its hash.
7. Keep the preflight gate fail-closed. No API request is permitted unless every parity/leak assertion passes.
8. Do not alter the dataset, equation/seed matrix, scoring, time cap, output schema, or historical result files.

## Scope and interpretation

This is a prompt-input parity amendment only. It does not claim that the two generation procedures are identical: HDS requests three candidates in one response and applies PySR refinement; Pure-LLM makes three separate single-formula calls and chooses among them by training R². Those differences remain explicit limitations of the comparison.

## Gate status

This document records the design decision. It does **not** mean the runner is already implementing the matched prompt. The live-call gate remains closed until the implementation, request-capture checks, and offline regression tests are merged and pass on the same commit.
