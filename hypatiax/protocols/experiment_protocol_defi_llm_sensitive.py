"""
experiment_protocol_defi_llm_sensitive.py

A benchmark designed to HAVE POWER to detect an LLM-prior benefit, if one exists.
It does not guarantee one. Design levers (all fixed BEFORE running any arm):

  1. Many more equations (21 llm_sensitive + 6 controls = 27) so the paired
     Wilcoxon test is not capped by tie-dominated data.
  2. Small, noisy training sets (60% of num_samples, 2% multiplicative noise,
     train only) so structure cannot be identified from data alone. Test is clean.
  3. Equations where a literature-known structure (piecewise kinks, N(d1),
     sqrt-price terms, fee-adjusted inputs) is hard for symbolic regression to
     rediscover from ~24 points, but is domain knowledge an LLM could recall.
  4. NEGATIVE CONTROLS: neutral-name synthetic formulas where no domain prior
     exists. The LLM should NOT help there. If it "helps" on controls, the
     effect is not a domain-knowledge effect (leakage/regularisation instead).
  5. Metadata flags `stratum` and `description_named` so the named-vs-neutral
     ablation can be run on the same equations.

Do not add, drop or edit equations after seeing results from any arm.
Recommended: num_samples=40, seeds {42, 99, 123, 7, 2024} (seeds reduce
variance per equation; they do not add independent units -- equations do).
"""
from __future__ import annotations

import math
import numpy as np

try:
    from scipy.stats import norm as _norm
    _pdf, _cdf, _ppf = _norm.pdf, _norm.cdf, _norm.ppf
except Exception:  # pragma: no cover
    _erf = np.vectorize(math.erf)
    _cdf = lambda x: 0.5 * (1 + _erf(np.asarray(x) / math.sqrt(2)))
    _pdf = lambda x: np.exp(-0.5 * np.asarray(x) ** 2) / math.sqrt(2 * math.pi)
    _ppf = None

try:  # only used to inherit generate_experiment_report; everything else is self-contained
    from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol as _Base
except Exception:
    try:
        from experiment_protocol_defi import DeFiExperimentProtocol as _Base
    except Exception:  # pragma: no cover
        _Base = object


# true functions keyed by ground-truth string; EVALUATOR SIDE ONLY (never pass to an LLM prompt).
# Filled when cases are generated (load_test_data), so rebuild cases to populate it.
FUNCS: dict = {}


PREREGISTRATION = {
    "unit_of_analysis": "equation (seed-averaged score per equation per arm)",
    "primary": "H (full HypatiaX) vs N (no-LLM), llm_sensitive stratum, "
               "paired Wilcoxon signed-rank, one-sided H>N",
    "secondary": ["H vs P (PySR only), llm_sensitive", "N vs P, llm_sensitive"],
    "control_check": "H vs N on controls stratum, two-sided, descriptive; "
                     "a significant benefit here invalidates a domain-knowledge reading",
    "correction": "Holm across the 3 llm_sensitive comparisons",
    "tie_threshold": 0.01,
    "failures": "report both: survivors-only and failures-as-worst",
    "report_regardless_of_outcome": True,
}


def min_informative_pairs(alpha: float = 0.05, k: int = 3) -> int:
    """Smallest n of same-direction informative pairs with exact one-sided
    Wilcoxon p = 2**-n below alpha/k (Holm's strictest step)."""
    n = 1
    while 2.0 ** -n >= alpha / k:
        n += 1
    return n   # alpha=0.05, k=3 -> 6


class DeFiLLMSensitiveProtocol(_Base):
    """Same interface as DeFiExperimentProtocol."""

    def __init__(self):
        if _Base is not object:
            super().__init__()
        self.domains = {
            "llm_sensitive": self._generate_sensitive_tests,
            "controls": self._generate_control_tests,
        }

    def get_all_domains(self) -> list[str]:
        return list(self.domains.keys())

    def load_test_data(self, domain: str, num_samples: int = 40) -> list[tuple]:
        if domain not in self.domains:
            raise ValueError(f"Unknown domain: {domain}")
        return self.domains[domain](num_samples)

    # ------------------------------------------------------------------
    @staticmethod
    def _make(name, fn, names, ranges, n, seed, stratum, truth,
              ext_var=None, ext_range=None, log=(), noise=0.02, named=True):
        rng = np.random.default_rng(seed)
        n_tr = int(round(0.6 * n))
        n_te = n - n_tr

        def draw(i, k, lo, hi):
            if i in log:
                return np.exp(rng.uniform(np.log(lo), np.log(hi), k))
            return rng.uniform(lo, hi, k)

        Xtr = np.column_stack([draw(i, n_tr, *r) for i, r in enumerate(ranges)])
        cols = []
        for i, r in enumerate(ranges):
            cols.append(draw(i, n_te, *ext_range) if i == ext_var else draw(i, n_te, *r))
        Xte = np.column_stack(cols)
        ytr = fn(*Xtr.T)
        yte = fn(*Xte.T)
        ytr = ytr * (1 + noise * rng.standard_normal(n_tr))   # noise: train only
        X = np.vstack([Xtr, Xte])
        y = np.concatenate([ytr, yte])
        assert np.all(np.isfinite(X)) and np.all(np.isfinite(y)), name
        FUNCS[truth] = fn
        meta = {
            "domain": stratum, "stratum": stratum, "ground_truth": truth,
            "extrapolation_test": ext_var is not None,
            "split_index": n_tr,            # rows [:n_tr] train (noisy), rest test (clean)
            "noise_frac_train": noise,
            "train_ranges": [list(map(float, r)) for r in ranges],
            "test_range_extrapolated_var": (
                {"var": names[ext_var], "range": list(map(float, ext_range))}
                if ext_var is not None else None),
            "description_named": named,
            "seed": seed,
        }
        return (name, X, y, names, meta)

    # ------------------------------------------------------------------
    def _generate_sensitive_tests(self, n: int) -> list[tuple]:
        K, R = 100.0, 0.04

        def d1(S, s, T):
            return (np.log(S / K) + (R + 0.5 * s ** 2) * T) / (s * np.sqrt(T))

        def bs_call(S, s, T):
            a = d1(S, s, T)
            return S * _cdf(a) - K * np.exp(-R * T) * _cdf(a - s * np.sqrt(T))

        def bs_put(S, s, T):
            a = d1(S, s, T)
            return K * np.exp(-R * T) * _cdf(-(a - s * np.sqrt(T))) - S * _cdf(-a)

        def es_normal(alpha, sigma):
            z = _ppf(alpha)
            return sigma * _pdf(z) / (1 - alpha)

        BSR = [(80, 120), (0.10, 0.50), (0.1, 1.0)]
        BSN = ["spot_price", "implied_volatility", "time_to_expiry"]
        M = self._make
        S = "llm_sensitive"
        c = [
            M("Uniswap V3 token0 amount in a tick range from liquidity and prices",
              lambda L, Pc, Pb: L * (1 / np.sqrt(Pc) - 1 / np.sqrt(Pb)),
              ["liquidity", "price_current", "price_upper"],
              [(1e3, 1e5), (1500, 2500), (2600, 3600)], n, 101, S,
              "L*(1/sqrt(Pc) - 1/sqrt(Pb))", 0, (1.2e5, 5e5), log=(0,)),
            M("Uniswap V3 token1 amount in a tick range from liquidity and prices",
              lambda L, Pc, Pa: L * (np.sqrt(Pc) - np.sqrt(Pa)),
              ["liquidity", "price_current", "price_lower"],
              [(1e3, 1e5), (1500, 2500), (1000, 1400)], n, 102, S,
              "L*(sqrt(Pc) - sqrt(Pa))", 0, (1.2e5, 5e5), log=(0,)),
            M("Black-Scholes European call option price",
              bs_call, BSN, BSR, n, 103, S, "S*N(d1) - K*exp(-rT)*N(d2)", 0, (125, 160)),
            M("Black-Scholes European put option price",
              bs_put, BSN, BSR, n, 104, S, "K*exp(-rT)*N(-d2) - S*N(-d1)", 0, (125, 160)),
            M("Black-Scholes call option delta",
              lambda S_, s, T: _cdf(d1(S_, s, T)), BSN, BSR, n, 105, S,
              "N(d1)", 0, (125, 160)),
            M("Constant product swap output amount including 0.3% fee",
              lambda x, y, dx: y * dx * 0.997 / (x + dx * 0.997),
              ["reserve_x", "reserve_y", "swap_in"],
              [(1e4, 1e5), (1e4, 1e5), (10, 5000)], n, 106, S,
              "y*dx*0.997/(x + 0.997*dx)", 2, (6000, 20000), log=(0, 1)),
            M("Annual percentage yield from APR with n compounding periods per year",
              lambda r, m: (1 + r / m) ** m - 1, ["apr", "periods_per_year"],
              [(0.02, 0.30), (1, 52)], n, 107, S, "(1 + r/m)**m - 1", 1, (100, 365)),
            M("Lending health factor with two collateral assets (LT 0.825 and 0.80)",
              lambda c1, c2, d: (c1 * 0.825 + c2 * 0.80) / d,
              ["collateral_a", "collateral_b", "debt"],
              [(1e3, 1e4), (1e3, 1e4), (2e3, 1.5e4)], n, 108, S,
              "(0.825*c1 + 0.80*c2)/d", 2, (1.6e4, 3e4)),
            M("Lending kinked borrow rate with optimal utilization 0.8",
              lambda u: np.where(u < 0.8, 0.04 * u / 0.8, 0.04 + 0.75 * (u - 0.8) / 0.2),
              ["utilization"], [(0.30, 0.95)], n, 109, S,
              "piecewise: 0.04*u/0.8 below kink, 0.04+0.75*(u-0.8)/0.2 above"),
            M("Expected shortfall of normal returns at confidence level alpha",
              es_normal, ["confidence_level", "volatility"],
              [(0.90, 0.99), (0.01, 0.10)], n, 110, S,
              "sigma*pdf(ppf(alpha))/(1-alpha)", 0, (0.992, 0.999)),
            M("Annualised Sharpe ratio from daily mean return and daily volatility",
              lambda mu, s: (mu - 0.00015) / s * np.sqrt(252),
              ["mean_daily_return", "daily_volatility"],
              [(0.0005, 0.003), (0.005, 0.03)], n, 111, S,
              "(mu - rf)/sigma*sqrt(252)", 1, (0.035, 0.06)),
            M("Perpetual long liquidation price with 0.5% maintenance margin",
              lambda e, lev: e * (1 - 1 / lev + 0.005),
              ["entry_price", "leverage"], [(1000, 4000), (2, 20)], n, 112, S,
              "entry*(1 - 1/lev + 0.005)", 1, (25, 50)),
            M("Price impact of a swap including 0.3% fee",
              lambda x, dx: dx * 0.997 / (x + dx * 0.997),
              ["reserve_x", "swap_in"], [(1e4, 1e5), (10, 5000)], n, 113, S,
              "0.997*dx/(x + 0.997*dx)", 1, (6000, 20000), log=(0,)),
            M("Uniswap V3 liquidity from token0 amount and price bounds",
              lambda x, Pa, Pb: x * np.sqrt(Pa * Pb) / (np.sqrt(Pb) - np.sqrt(Pa)),
              ["token0_amount", "price_lower", "price_upper"],
              [(1, 100), (1500, 2000), (2200, 3000)], n, 114, S,
              "x*sqrt(Pa*Pb)/(sqrt(Pb)-sqrt(Pa))", 0, (150, 500)),
            M("Continuously compounded staking yield over a holding period",
              lambda r, t: np.exp(r * t) - 1, ["apr", "years"],
              [(0.02, 0.40), (0.1, 2.0)], n, 115, S, "exp(r*t) - 1", 1, (3.0, 6.0)),
            M("Geometric mean price of two assets",
              lambda p1, p2: np.sqrt(p1 * p2), ["price_a", "price_b"],
              [(0.5, 2.0), (0.5, 2.0)], n, 116, S, "sqrt(p1*p2)", 0, (3.0, 6.0)),
            M("Minimum variance hedge ratio",
              lambda rho, sa, sb: rho * sa / sb,
              ["correlation", "vol_asset", "vol_hedge"],
              [(0.2, 0.95), (0.3, 0.9), (0.3, 0.9)], n, 117, S,
              "rho*sa/sb", 1, (1.0, 1.6)),
            M("Days of fee income needed to break even on impermanent loss",
              lambda r, apr: (1 - 2 * np.sqrt(r) / (1 + r)) / (apr / 365),
              ["price_ratio", "fee_apr"], [(0.5, 2.0), (0.10, 0.80)], n, 118, S,
              "(1 - 2*sqrt(r)/(1+r))/(apr/365)", 0, (2.5, 4.0)),
            M("Uniswap V3 capital efficiency multiplier of a price range",
              lambda Pa, Pb: 1 / (1 - (Pa / Pb) ** 0.25),
              ["price_lower", "price_upper"], [(1000, 1800), (2200, 3000)], n, 119, S,
              "1/(1 - (Pa/Pb)**0.25)", 1, (3500, 6000)),
            M("Fractional collateral price drop that triggers liquidation (LT 0.825)",
              lambda col, debt: 1 - debt / (0.825 * col),
              ["collateral_value", "debt"], [(4e4, 1e5), (1e3, 1.5e4)], n, 120, S,
              "1 - debt/(0.825*collateral)", 1, (1.8e4, 3e4)),
            M("Value of a Uniswap V2 LP position from invariant k and price",
              lambda k, P: 2 * np.sqrt(k * P), ["invariant_k", "price"],
              [(1e6, 1e8), (500, 3000)], n, 121, S, "2*sqrt(k*P)", 1, (4000, 9000),
              log=(0,)),
        ]
        return c

    # ------------------------------------------------------------------
    def _generate_control_tests(self, n: int) -> list[tuple]:
        S = "controls"
        r = [(0.5, 3.0)] * 4
        M = self._make
        defs = [
            ("C1", lambda a, b, c, d: a * b / (c + d), "x0*x1/(x2+x3)"),
            ("C2", lambda a, b, c, d: np.sqrt(a) * b - c ** 2, "sqrt(x0)*x1 - x2**2"),
            ("C3", lambda a, b, c, d: np.log(1 + a * b) / c, "log(1+x0*x1)/x2"),
            ("C4", lambda a, b, c, d: a * np.exp(-b) + c, "x0*exp(-x1) + x2"),
            ("C5", lambda a, b, c, d: a ** 2 + 3 * b, "x0**2 + 3*x1"),
            ("C6", lambda a, b, c, d: (a - b) / (a + b + 1), "(x0-x1)/(x0+x1+1)"),
        ]
        return [
            M(f"Synthetic benchmark function {nm} with no domain prior", fn,
              ["x0", "x1", "x2", "x3"], r, n, 201 + i, S, tr, 0, (3.5, 6.0),
              named=False)
            for i, (nm, fn, tr) in enumerate(defs)
        ]


if __name__ == "__main__":
    p = DeFiLLMSensitiveProtocol()
    tot = 0
    for d in p.get_all_domains():
        t = p.load_test_data(d, 40)
        tot += len(t)
        print(d, len(t), "cases")
    print("total", tot, "| min same-direction informative pairs for Holm(3):",
          min_informative_pairs())
