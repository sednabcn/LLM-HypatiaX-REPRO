
# HypatiaX Analysis Report — `exp1b`

Experiment mode: **standard**
N total: 72 | N standard: 72 | N intractable: 0
R² success threshold: 0.8

## ✅ No Fatal Conditions


## Method Summary (standard equations only)

| Method | N | Success% (flag) | R²≥0.80% | Median test R² | Mean test R² |
|--------|---|-----------------|----------|----------------|--------------|
| Pure LLM | 72 | 81.9% | 82.8% | 1.0000 | -0.2194 |
| Neural Net | 72 | 90.3% | 20.0% | -0.2412 | -1.0878 |
| Hybrid | 72 | 100.0% | 90.3% | 1.0000 | 0.9048 |

## Mann-Whitney U Tests (two-sided, clipped R², standard equations)


### Hybrid vs Pure LLM

  U=2357.0,  p=0.0587,  direction=b_greater,  n=(72, 58)

### Hybrid vs Neural Net

  U=4504.0,  p=0.0000**,  direction=a_greater,  n=(72, 65)

### Neural Net vs Pure LLM

  U=550.0,  p=0.0000**,  direction=b_greater,  n=(65, 58)
_** = p < 0.05_

## Hybrid vs Neural Net (head-to-head, equation level)

Equations with both finite R²: 65
Hybrid wins:  59  (90.8%)
NN wins:      0
Tied:         6

## Coverage Gaps (15 equations with best R² < 0.8)

| Equation | Difficulty | Type | Best R² | LLM | NN | Hybrid |
|----------|------------|------|---------|-----|----|----|
| Black-Scholes Call Price | hard | norm_cdf | N/A | N/A | -0.8981 | -0.8981 |
| Black-Scholes Put Price | hard | norm_cdf | N/A | N/A | 0.0459 | 0.0459 |
| Capital efficiency | medium | rational | N/A | N/A | -2.0963 | 1.0000 |
| Component ES | hard | quadratic_form | N/A | N/A | -0.2542 | 1.0000 |
| Liquidation Price Long | medium | rational | N/A | N/A | 0.8965 | 1.0000 |
| Liquidation Price Short | medium | rational | N/A | N/A | -2.5432 | 1.0000 |
| Liquidation price for leveraged long | hard | rational | N/A | N/A | 0.6256 | 1.0000 |
| Liquidation price for leveraged short | hard | rational | N/A | N/A | -1.4329 | 1.0000 |
| Maximum safe leverage | hard | rational | N/A | N/A | -1.3461 | 1.0000 |
| Optimal LP Position (Kelly) | medium | rational | N/A | N/A | 0.0000 | 0.0000 |
| Options Delta | medium | norm_cdf | N/A | N/A | -10.3199 | 0.7709 |
| Required collateral | hard | rational | N/A | N/A | -0.7895 | 1.0000 |
| Theta of option | hard | norm_pdf | N/A | N/A | -0.7755 | -0.7755 |
| Vega of option | hard | norm_pdf | 0.6593 | 0.5695 | 0.6593 | 0.6593 |
| Portfolio Expected Shortfall for correlated | hard | quadratic_form | N/A | N/A | N/A | 1.0000 |

## R²≥0.80 Rate by Difficulty

| Difficulty | N | LLM R²≥0.80 | NN R²≥0.80 | Hybrid R²≥0.80 |
|------------|---|-------------|------------|----------------|
| easy | 24 | 87.5% | 14.3% | 100.0% |
| hard | 20 | 81.8% | 11.1% | 75.0% |
| medium | 28 | 78.3% | 30.8% | 92.9% |

## Median Test R² by Formula Type

| Formula Type | N | LLM median R² | NN median R² | Hybrid median R² |
|--------------|---|---------------|--------------|------------------|
| algebraic | 4 | 1.0000 | -1.5028 | 1.0000 |
| algebraic_with_sqrt | 4 | 1.0000 | -0.4518 | 1.0000 |
| exponential | 5 | 1.0000 | -2.1634 | 1.0000 |
| linear | 18 | 1.0000 | -1.3664 | 1.0000 |
| norm_cdf | 3 | N/A | -0.8981 | 0.0459 |
| norm_pdf | 3 | 0.7830 | 0.3433 | 0.3433 |
| piecewise_linear | 1 | -3.5798 | 0.8679 | 1.0000 |
| quadratic_form | 2 | N/A | -0.2542 | 1.0000 |
| rational | 24 | 1.0000 | -0.0229 | 1.0000 |
| rational_simple | 7 | 1.0000 | 0.5461 | 1.0000 |
| weighted_aggregate | 1 | 1.0000 | 0.9725 | 1.0000 |

## Extrapolation Gap (train R² − test R²)

| Method | Mean gap | Median gap | N |
|--------|----------|------------|---|
| Pure LLM | -172.6498 | 0.0000 | 58 |
| Neural Net | 2.0881 | 1.2411 | 65 |
| Hybrid | -0.1778 | 0.0000 | 71 |

## Wall-clock Timing (standard equations)

| Method | Mean (s) | Median (s) | Total (s) | N |
|--------|----------|------------|-----------|---|
| Pure LLM | 11.0177 | 9.9095 | 793.27 | 72 |
| Neural Net | 0.2954 | 0.3270 | 21.27 | 72 |
| Hybrid | 1.8920 | 1.3360 | 136.22 | 72 |

## Hybrid Routing Decisions

| Decision | Count |
|----------|-------|
| llm | 66 |
| nn | 5 |
| nn_fallback | 1 |
