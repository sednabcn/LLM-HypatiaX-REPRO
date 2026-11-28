# Reusable formula audit utilities

Import the shared API wherever an experiment needs formula auditing:

```python
from hypatiax.experiments.audit import (
    audit_formula,
    compare_callables,
    validate_formula_metadata,
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

Symbolic and numerical outcomes are intentionally separate. Numerical agreement is not proof of symbolic identity, and high predictive R² is not proof of either.

## Safety and interpretation

The symbolic evaluator uses an AST allowlist and does not execute generated Python. Supply an authoritative ground-truth expression, exact variable mapping, and constants. Missing answer keys or incomplete mappings must remain not assessable; do not infer ground truth from benchmark scores.

The numerical helper invokes the callables supplied to it. Only pass trusted callables created by your own application, never dynamically execute model-generated code to create them. Choose points that cover relevant domains and singularities; this helper does not establish domain equivalence or prove behavior outside the supplied points.
