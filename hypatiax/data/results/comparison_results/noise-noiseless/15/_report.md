
# HypatiaX Analysis Report — `exp1b`

Experiment mode: **standard**
N total: 3 | N standard: 3 | N intractable: 0
R² success threshold: 0.8

## ✅ No Fatal Conditions


## Method Summary (standard equations only)

| Method | N | Success% (flag) | R²≥0.80% | Median test R² | Mean test R² |
|--------|---|-----------------|----------|----------------|--------------|
| Pure LLM | 3 | 66.7% | 100.0% | 1.0000 | 1.0000 |
| Neural Net | 3 | 66.7% | 0.0% | -1.4090 | -1.4090 |
| Hybrid | 3 | 100.0% | 100.0% | 1.0000 | 1.0000 |

## Mann-Whitney U Tests (two-sided, clipped R², standard equations)


### Hybrid vs Pure LLM

  U=3.5,  p=1.0000,  direction=b_greater,  n=(3, 2)

### Hybrid vs Neural Net

  U=6.0,  p=0.1386,  direction=a_greater,  n=(3, 2)

### Neural Net vs Pure LLM

  U=0.0,  p=0.3333,  direction=b_greater,  n=(2, 2)
_** = p < 0.05_

## Hybrid vs Neural Net (head-to-head, equation level)

Equations with both finite R²: 2
Hybrid wins:  2  (100.0%)
NN wins:      0
Tied:         0

## Coverage Gaps (1 equations with best R² < 0.8)

| Equation | Difficulty | Type | Best R² | LLM | NN | Hybrid |
|----------|------------|------|---------|-----|----|----|
| Portfolio Expected Shortfall for correlated | hard | quadratic_form | N/A | N/A | N/A | 1.0000 |

## R²≥0.80 Rate by Difficulty

| Difficulty | N | LLM R²≥0.80 | NN R²≥0.80 | Hybrid R²≥0.80 |
|------------|---|-------------|------------|----------------|
| easy | 1 | 100.0% | 0.0% | 100.0% |
| hard | 1 | 0.0% | 0.0% | 100.0% |
| medium | 1 | 100.0% | 0.0% | 100.0% |

## Median Test R² by Formula Type

| Formula Type | N | LLM median R² | NN median R² | Hybrid median R² |
|--------------|---|---------------|--------------|------------------|
| algebraic | 1 | 1.0000 | -2.7952 | 1.0000 |
| quadratic_form | 1 | N/A | N/A | 1.0000 |
| rational | 1 | 1.0000 | -0.0229 | 1.0000 |

## Extrapolation Gap (train R² − test R²)

| Method | Mean gap | Median gap | N |
|--------|----------|------------|---|
| Pure LLM | 0.0000 | 0.0000 | 2 |
| Neural Net | 2.4089 | 2.4089 | 2 |
| Hybrid | 0.0000 | 0.0000 | 3 |

## Wall-clock Timing (standard equations)

| Method | Mean (s) | Median (s) | Total (s) | N |
|--------|----------|------------|-----------|---|
| Pure LLM | 14.9987 | 11.3860 | 45.0 | 3 |
| Neural Net | 0.1580 | 0.2340 | 0.47 | 3 |
| Hybrid | 1.8260 | 1.7070 | 5.48 | 3 |

## Hybrid Routing Decisions

| Decision | Count |
|----------|-------|
| llm | 3 |
