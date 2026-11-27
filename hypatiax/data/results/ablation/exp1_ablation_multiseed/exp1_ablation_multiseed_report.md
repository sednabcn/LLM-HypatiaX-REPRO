# Exp1 Core-15 five-seed descriptive summary

- Equation families: 15
- Repeated seeds: 42, 99, 123, 777, 2024
- Preserved arm records: 225
- Source revision: 1bb4c9d7ccf4813b10014fc85a67b4a28d8f18c4
- Benchmark script SHA-256: 5a5eae79a57eeee3d0fcfd01f2dcf48fb2bfe5c924560db1a278891491fa0d70

## Per-seed results

| Seed | Arm | Successful test rows | Mean test R² | Mean far-OOD R² | Mean wall time (s) |
|---:|---|---:|---:|---:|---:|
| 42 | pysr_only | 15 | 0.9783 | -4.7821 | 1104.3844 |
| 42 | hypatia | 15 | 0.9929 | 0.2885 | 350.8632 |
| 42 | hypatia_nollm | 15 | 0.9924 | 0.5742 | 469.7969 |
| 99 | pysr_only | 15 | 0.9711 | -4.2666 | 1079.3666 |
| 99 | hypatia | 15 | 0.9365 | -0.2703 | 404.5588 |
| 99 | hypatia_nollm | 15 | 0.9365 | -0.2713 | 567.5701 |
| 123 | pysr_only | 15 | 0.9860 | -4.3811 | 1063.4976 |
| 123 | hypatia | 15 | 0.9939 | 0.9988 | 333.9910 |
| 123 | hypatia_nollm | 15 | 0.9942 | 0.5326 | 430.6778 |
| 777 | pysr_only | 15 | 0.9964 | -6.3955 | 1061.1915 |
| 777 | hypatia | 15 | 0.9343 | -6.8519 | 603.9060 |
| 777 | hypatia_nollm | 15 | 0.9169 | -1.0575 | 698.8795 |
| 2024 | pysr_only | 15 | 0.9855 | -5.3403 | 1105.5289 |
| 2024 | hypatia | 15 | 0.9859 | -0.8321 | 375.9960 |
| 2024 | hypatia_nollm | 15 | 0.9873 | 0.9502 | 475.2745 |

## Across-seed descriptive contrasts

| Contrast | Seeds with paired data | Mean of seed-level mean Δ far-R² | Sample SD |
|---|---:|---:|---:|
| hypatia_vs_pysr | 5 | -1.4108 | 2.7387 |
| hypatia_vs_nollm | 5 | -1.4791 | 2.5550 |
| nollm_vs_pysr | 5 | 0.1735 | 0.8200 |

## Interpretation and limits

The 15 equation families are measured repeatedly across five seeds. The 75 equation-seed units are not 75 independent equation families. This report therefore gives descriptive seed-level means and sample standard deviations only; it performs no pooled significance test.
Failed primary evaluations remain visible in the case/seed CSV and are excluded from successful metric summaries. H−N estimates the incremental effect of enabling the LLM within the Hybrid pipeline, not a standalone Pure-LLM effect.
