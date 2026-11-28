# Reusable formula audit utilities

Import the shared API wherever an experiment needs formula auditing:

```python
from hypatiax.experiments.audit import (
    audit_formula,
    compare_callables,
    validate_formula_metadata,
    validate_generated_formula,
)

metadata = validate_formula_metadata(
    predicted_formula,
    variable_names=["reserve", "utilization"],
    constants={"SECONDS_PER_YEAR": 31_536_000},
)
if metadata["valid"]:
    symbolic = audit_formula(
        predicted_formula,
        ground_truth_expression,
        variable_names=["reserve", "utilization"],
        constants={"SECONDS_PER_YEAR": 31_536_000},
    )
```

## Separate questions, separate statuses

- `audit_formula` checks formal symbolic identity with the existing restricted AST/SymPy evaluator. It does not use predictive R².
- `compare_callables` checks numerical agreement at caller-supplied points. It accepts trusted Python callables only; it never evaluates generated source strings.
- `validate_formula_metadata` checks required source, variable, and numeric-constant metadata without executing formula text.
- `validate_generated_formula` is the fail-closed, offline gate for a generated formula against an authoritative ground-truth expression. It reuses the restricted symbolic adjudicator and only treats a formula as exact-match eligible when strict symbolic equivalence is established.

## Validating generated formulas

Use `validate_generated_formula` for future generated outputs, not to rewrite or retroactively alter historical benchmark records. The gate is deterministic and offline: it does not train models, launch experiments, or call an LLM/provider.

A meaningful assessment requires the formula text, an authoritative ground-truth expression, and an explicit variable schema. Supply source-backed aliases and constants when the source defines them; do not infer aliases, constants, or answer keys from generated output or benchmark scores. For the DeFi 40/60 contracts, source-backed Theta constants include `K=100.0` and `r=0.04`; equation-specific aliases are documented in the adjudication report.

Interpret the gate conservatively:

| Outcome | Meaning | Exact-match treatment |
|---|---|---|
| Equivalent | The restricted symbolic evaluator establishes strict symbolic identity under the supplied schema and source-backed substitutions. | Eligible for exact match |
| Not equivalent | The formula is assessable, but strict symbolic identity is not established. | Not an exact match |
| Not assessable | Syntax is malformed, required schema/source information is missing, or the evaluator cannot safely assess the expression. | Remains not assessable; never silently pass |

Strict symbolic identity is the primary exact-match criterion. Numerical agreement at sampled points, a high R² score, or equivalence only on a restricted positive/negative domain does not establish unrestricted symbolic identity. If domain-limited equivalence is relevant, report it separately and state the domain assumptions; do not promote it to strict symbolic equivalence.

## Safety and interpretation

The symbolic evaluator uses an AST allowlist and does not execute generated Python. Supply an authoritative ground-truth expression, exact variable mapping, and constants. Missing answer keys or incomplete mappings must remain not assessable; do not infer ground truth from benchmark scores.

The numerical helper invokes the callables supplied to it. Only pass trusted callables created by your own application, never dynamically execute model-generated code to create them. Choose points that cover relevant domains and singularities; this helper does not establish domain equivalence or prove behavior outside the supplied points.

## DeFi 40/60 reference

The source-backed adjudication and alias decisions are documented in [the DeFi 40/60 source-backed alias adjudication report](../../../research/reports/defi-4060-source-backed-alias-adjudication-2026-11-28.md). The offline CI contract is defined in `.github/workflows/defi_4060_contracts.yml` and covers artifact integrity, source-backed formulas, units/output semantics, generated-formula gating, remaining mismatch families, and Theta/domain contracts.
