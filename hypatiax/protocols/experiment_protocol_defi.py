import os as _os
import pathlib as _pathlib
import sys as _sys

# ── sys.path bootstrap ────────────────────────────────────────────────────
# Ensures hypatiax.* imports resolve whether this file is run directly
# or imported by run_all_checkpoint.py.
_proto_dir  = _pathlib.Path(__file__).resolve().parent
_repo_root  = _pathlib.Path(_os.environ.get("REPRO_ROOT", str(_proto_dir.parent)))
for _p in [str(_repo_root), str(_repo_root / "hypatiax")]:
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
del _os, _pathlib, _sys, _proto_dir, _repo_root, _p


import numpy as np


class DeFiExperimentProtocol:
    """Enhanced DeFi experiment protocol with fixed formulas"""

    def __init__(self):
        self.domains = {
            # ── canonical names ──────────────────────────────────────────────
            "amm": self._generate_amm_tests,
            "risk_var": self._generate_var_tests,
            "liquidity": self._generate_liquidity_tests,
            "expected_shortfall": self._generate_es_tests,
            "liquidation": self._generate_liquidation_tests,
            "portfolio_variance": self._generate_portfolio_variance_tests,
            # ── aliases used by test_enhanced_defi_extrapolation.py ──────────
            # "risk"        → combined VaR + ES tests
            "risk": self._generate_risk_alias_tests,
            # "lending"     → collateral-ratio / LTV tests
            "lending": self._generate_lending_tests,
            # "staking"     → APY / compounding tests
            "staking": self._generate_staking_tests,
            # "trading"     → leverage / liquidation-price tests
            "trading": self._generate_trading_tests,
            # "derivatives" → options / Black-Scholes tests
            "derivatives": self._generate_derivatives_tests,
        }

    @staticmethod
    def _apply_shard_ids(domains: list[str]) -> list[str]:
        """Filter *domains* to those listed in the SHARD_IDS environment variable.

        SHARD_IDS: space- or comma-separated domain names
        (e.g. ``"amm risk_var"`` or ``"amm,risk_var"``).
        Falls back to the full domain list when the variable is unset or empty
        (local / Colab runs).

        This mirrors the ``_apply_task_ids_defi`` two-stage pattern in
        hypatiax_defi_benchmark_v3c.py.  The fallback is intentionally SILENT:
        for exp1b, SHARD_IDS contains synthetic checkpoint-tracking IDs such as
        ``"portfolio_seed42"`` which match no domain name — that is correct
        behaviour, not a misconfiguration.  Emitting a RuntimeWarning here
        would be actively misleading, so the fallback is silent.

        For exp1 / suppA, SHARD_IDS = domain keys (e.g. ``"amm risk_var"``),
        which match exactly and produce the correct disjoint domain subset.
        """
        import os

        raw = os.environ.get("SHARD_IDS", "").replace(",", " ").split()
        if not raw:
            return domains           # unset → local / Colab run, no filtering
        allowed = set(raw)
        filtered = [d for d in domains if d in allowed]
        if not filtered:
            # No domain-key match — SHARD_IDS are synthetic checkpoint IDs
            # (exp1b pattern) or genuinely stale.  Silent fallback: actual
            # case filtering is handled by DEFI_TASK_FILTER in run_benchmark().
            return domains
        return filtered

    def get_all_domains(self) -> list[str]:
        """Get all available domains, filtered by SHARD_IDS if set."""
        return self._apply_shard_ids(list(self.domains.keys()))

    def load_test_data(self, domain: str, num_samples: int = 100) -> list[tuple]:
        """Load test data for a domain"""
        if domain not in self.domains:
            raise ValueError(f"Unknown domain: {domain}")
        return self.domains[domain](num_samples)

    def get_cases(self):
        """Return the flattened case catalogue expected by portfolio benchmark scripts.

        The portfolio variance benchmark calls ``proto.get_cases()`` and then indexes
        into the result to find the portfolio case. Older protocols do not expose
        this interface, so we add a compatibility layer that flattens every domain
        into the same simple case schema used elsewhere in the repo.
        """
        cases = []
        for domain in self.get_all_domains():
            for test in self.load_test_data(domain, num_samples=200):
                name, _, _, variables, metadata = test
                cases.append(
                    {
                        "name": name,
                        "description": name,
                        "domain": domain,
                        "variables": list(variables),
                        "metadata": dict(metadata or {}),
                    }
                )
        return cases

    def build_train_test_split(self, case_index):
        """Return a 50/50 train/test split for the case at *case_index*."""
        cases = self.get_cases()
        if case_index < 0 or case_index >= len(cases):
            raise IndexError(f"Case index {case_index} out of range for {len(cases)} cases")

        selected = cases[case_index]
        domain = selected["domain"]
        case_name = selected["name"]

        for name, X, y, _, _ in self.load_test_data(domain, num_samples=200):
            if name == case_name:
                split = max(1, len(X) // 2)
                return X[:split], y[:split], X[split:], y[split:]

        raise RuntimeError(f"Case '{case_name}' not found in domain '{domain}'")

    def _generate_portfolio_variance_tests(self, n: int) -> list[tuple]:
        """Portfolio variance test case used by the CI benchmark script."""
        np.random.seed(42)
        asset_a = np.linspace(10000.0, 1000000.0, n)
        asset_b = np.linspace(5000.0, 500000.0, n)
        corr = np.linspace(-0.5, 0.9, n)
        portfolio_var = np.sqrt(asset_a**2 + asset_b**2 + 2.0 * corr * asset_a * asset_b)

        return [
            (
                "Portfolio Variance of two correlated assets",
                np.column_stack([asset_a, asset_b, corr]),
                portfolio_var,
                ["asset_a", "asset_b", "correlation"],
                {
                    "domain": "portfolio_variance",
                    "ground_truth": "sqrt(asset_a**2 + asset_b**2 + 2*rho*asset_a*asset_b)",
                    "extrapolation_test": False,
                },
            )
        ]

    # ========================================================================
    # AMM DOMAIN
    # ========================================================================
