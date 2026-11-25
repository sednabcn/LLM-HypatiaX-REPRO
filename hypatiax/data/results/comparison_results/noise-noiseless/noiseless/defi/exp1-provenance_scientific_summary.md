# Exp1 five-seed scientific summary

- Unique equation families: 74
- Preserved seed/equation records: 370
- Seeds: 42, 99, 123, 777, 2024
- Repeated seeds are not counted as independent equation families.
- Undefined metrics and intractable cases remain explicit in the CSV and JSON.

## Per-seed results

| Seed | NN median test R² | Hybrid median test R² | NN mean clipped R² [-10,1] | Hybrid mean clipped R² [-10,1] | Paired n | Better / tie / worse |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | 0.999020 | 0.999106 | 0.834892 | 0.846173 | 73 | 16 / 57 / 0 |
| 99 | 0.998731 | 0.998764 | 0.849418 | 0.854680 | 72 | 12 / 60 / 0 |
| 123 | 0.997828 | 0.998783 | 0.864102 | 0.877010 | 73 | 15 / 58 / 0 |
| 777 | 0.998754 | 0.999056 | 0.866198 | 0.870885 | 73 | 13 / 60 / 0 |
| 2024 | 0.998694 | 0.999032 | 0.847101 | 0.861019 | 73 | 12 / 61 / 0 |

## Interpretation limits

The 370 rows are 74 repeated equation families measured under five seeds; seeds are repeated runs, not 370 independent equation families. Cross-seed summaries are calculated within equation_id. Clipped R² uses [-10, 1] and is reported separately from raw R².
The paired delta counts are descriptive only; no inferential test treats seeds as independent samples.
