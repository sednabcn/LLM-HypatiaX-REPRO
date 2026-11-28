#!/usr/bin/env python3
"""Read-only source-backed alias adjudication for committed DeFi 40/60 results."""
from __future__ import annotations
import argparse, ast, json, re
from collections import Counter, defaultdict
from pathlib import Path
try:
    from audit_4060_reusable import SEEDS, load_records
except ModuleNotFoundError:
    from scripts.analysis.audit_4060_reusable import SEEDS, load_records
from hypatiax.experiments.audit import audit_formula

SOURCE = "hypatiax/protocols/experiment_protocol_defi.py"
# Equation-specific shorthand-to-schema mappings taken from the protocol generator.
ALIASES = {
 "AMM output amount":{"x":"reserve_x","y":"reserve_y"},
 "Annualised Portfolio tracking error":{"daily_te":"daily_tracking_error"},
 "Black-Scholes Call Price":{"S":"spot_price","K":"strike","r":"risk_free_rate","sigma":"implied_volatility","T":"time_to_expiry"},
 "Black-Scholes Put Price":{"S":"spot_price","K":"strike","r":"risk_free_rate","sigma":"implied_volatility","T":"time_to_expiry"},
 "Borrow APY from utilization":{"utilization":"utilization_rate"},
 "Borrowing Interest":{"rate":"interest_rate","t":"time_years"},
 "Call option intrinsic":{"S":"spot_at_expiry","K":"strike"},
 "Capital efficiency":{"P_upper":"price_upper","P_lower":"price_lower"},
 "Collateral ratio":{"collateral":"collateral_value","borrowed":"borrowed_value"},
 "Component ES":{"ES":"individual_es"},
 "Compounding Staking Returns":{"n":"compounds_per_year"},
 "Concentrated liquidity position width":{"P_upper":"price_upper","P_lower":"price_lower"},
 "Concentrated liquidity position width (v2)":{"P_upper":"price_upper","P_lower":"price_lower"},
 "Constant Product Price Impact":{"dx":"swap_amount","x":"reserve_x"},
 "Constant product formula":{"k":"invariant_k","x":"reserve_x"},
 "Constant product formula (multivariate)":{"k":"invariant_k","x":"reserve_x","y":"reserve_y"},
 "Convexity Adjustment":{"spot":"spot_price"},
 "Correlated Portfolio VaR":{"var1":"var_asset1","var2":"var_asset2","rho":"correlation"},
 "Effective Leverage":{"L":"initial_leverage","delta_p":"price_change_pct"},
 "Expected Shortfall at 95%":{"portfolio":"portfolio_value","volatility":"daily_volatility"},
 "Expected Shortfall at 99%":{"portfolio":"portfolio_value","volatility":"daily_volatility"},
 "Forward price for derivative":{"r":"risk_free_rate","q":"div_yield","T":"maturity"},
 "Funding rate cost (extended)":{"mark":"mark_price","index":"index_price"},
 "Gamma of option":{"S":"spot_price","K":"strike","r":"risk_free_rate","sigma":"implied_volatility","T":"time_to_expiry"},
 "Health factor":{"collateral":"collateral_value"},
 "Impermanent loss in constant product":{"r":"price_ratio"},
 "Impermanent loss percentage":{"r":"price_ratio"},
 "Incremental VaR":{"v1":"portfolio_var","v2":"position_var","rho":"correlation"},
 "LP fee earnings":{"liq_provided":"liquidity_provided","pool_liq":"pool_liquidity"},
 "LP share percentage":{"deposit":"lp_deposit"},
 "Loan-to-Value":{"loan":"loan_amount"},
 "Maximum safe leverage":{"loss_pct":"acceptable_loss_pct"},
 "Multi-Collateral LTV":{"collat_a":"collateral_a","collat_b":"collateral_b"},
 "Multi-day Value at Risk":{"days":"time_horizon_days"},
 "Optimal LP Position (Kelly)":{"mu":"expected_fee_apy","sigma":"il_risk"},
 "Options Delta":{"m":"moneyness","vol":"implied_volatility","T":"time_to_expiry"},
 "Partial liquidation amount":{"fee":"liquidation_fee"},
 "Portfolio Expected Shortfall for correlated":{"ES1":"position1_es","ES2":"position2_es","rho":"correlation"},
 "Portfolio VaR for two correlated":{"var1":"var_asset1","var2":"var_asset2","rho":"correlation"},
 "Position margin ratio":{"upnl":"unrealised_pnl"},
 "Price slippage percentage":{"dx":"trade_dx","x":"reserve_x"},
 "Put-call parity":{"S":"spot","T":"maturity"},
 "Simple options moneyness":{"S":"spot_price"},
 "Slashing penalty":{"staked":"staked_amount"},
 "Staking reward for fixed lock-up":{"staked":"staked_amount","days":"lock_days"},
 "Supply APY from borrow":{"util":"utilization"},
 "Theta of option":{"S":"spot_price","K":"strike","r":"risk_free_rate","sigma":"implied_volatility","T":"time_to_expiry"},
 "Uniswap V3 virtual":{"amount":"token_amount","P_upper":"price_upper","P_lower":"price_lower"},
 "Utilization rate of DeFi":{"borrowed":"total_borrowed","supplied":"total_supplied"},
 "Validator commission adjusted":{"commission":"commission_rate"},
 "Value at Risk at 95%":{"volatility":"daily_volatility"},
 "Value at Risk at 99%":{"volatility":"daily_volatility"},
 "Vega of option":{"S":"spot_price","K":"strike","r":"risk_free_rate","sigma":"implied_volatility","T":"time_to_expiry"},
}

def expand_source_defined_d1_d2(equation, expression):
    """Inline d1/d2 exactly as defined by the original Black-Scholes protocol."""
    eligible = {
        "Black-Scholes Call Price", "Black-Scholes Put Price",
        "Gamma of option", "Vega of option", "Theta of option",
    }
    if equation not in eligible:
        return expression
    expression = expression.replace("rT", "r * T")
    d1 = "((log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T)))"
    d2 = "(" + d1 + " - sigma * sqrt(T))"
    replacements = {"d1": d1, "d2": d2}

    class InlineDerived(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id in replacements:
                return ast.copy_location(
                    ast.parse(replacements[node.id], mode="eval").body, node
                )
            return node

    tree = ast.parse(expression, mode="eval")
    tree = InlineDerived().visit(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree.body)


def adjudicate(protocol, records):
    grouped = defaultdict(list)
    for rec in records:
        eq = str(rec.get("equation_id"))
        ctx = rec.get("formula_context") or {}
        vars_ = ctx.get("variable_names")
        constants = ctx.get("constants") if isinstance(ctx.get("constants"), dict) else {}
        aliases = dict(ctx.get("ground_truth_aliases") or {})
        aliases.update(ALIASES.get(eq, {}))
        allowed = set(vars_ or []) | set(constants)
        invalid = {a: c for a, c in aliases.items() if c not in allowed}
        aliases = {a: c for a, c in aliases.items() if c in allowed}
        result = audit_formula(
            (rec.get("results") or {}).get("hybrid", {}).get("formula"),
            expand_source_defined_d1_d2(eq, ctx.get("ground_truth_expression")),
            vars_ if isinstance(vars_, list) else None,
            aliases, constants)
        grouped[eq].append({
            "seed": rec.get("seed"), "status": result.get("status"),
            "reason": result.get("reason"), "aliases": aliases,
            "invalid_aliases": invalid})

    families, totals = [], Counter()
    for eq, cases in sorted(grouped.items()):
        counts = Counter(c["status"] for c in cases)
        totals.update(counts)
        families.append({
            "equation_id": eq, "status_counts": dict(counts),
            "universally_equivalent": counts == {"exact_symbolic_equivalent": len(cases)},
            "cases": cases})
    return {"protocol": protocol, "record_count": len(records),
            "equation_count": len(families), "status_counts": dict(totals),
            "universally_equivalent_families": sum(x["universally_equivalent"] for x in families),
            "families": families}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--output-md", type=Path, required=True)
    args = ap.parse_args()
    protocols = [adjudicate(n, load_records(n)) for n in ("random", "pca")]
    report = {"schema_version": 1, "seeds": list(SEEDS), "read_only": True,
              "experiments_rerun": False, "llm_calls": 0, "source_file": SOURCE,
              "alias_policy": "equation-specific aliases; targets must exist in saved variable_names or constants",
              "aliases": ALIASES, "protocols": protocols}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = ["# DeFi 40/60 source-backed alias adjudication", "",
      "Read-only analysis of committed result JSON. No experiments, training, or LLM calls; no historical records or formulas edited.", "",
      "Alias source: " + SOURCE + ". Canonical targets are validated against each saved variable schema/constants.", "",
      "| Protocol | Records | Families | Exact | Not assessable | Not equivalent | Exact families |",
      "|---|---:|---:|---:|---:|---:|---:|"]
    for p in protocols:
        c = p["status_counts"]
        lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            p["protocol"], p["record_count"], p["equation_count"],
            c.get("exact_symbolic_equivalent", 0), c.get("not_assessable", 0),
            c.get("not_symbolically_equivalent", 0), p["universally_equivalent_families"]))
    for p in protocols:
        lines += ["", "## " + p["protocol"], ""]
        for fam in p["families"]:
            if fam["universally_equivalent"] and not any(x["aliases"] for x in fam["cases"]):
                continue
            lines += ["### " + fam["equation_id"], "",
                      "- Status counts: " + json.dumps(fam["status_counts"], sort_keys=True)]
            if fam["cases"] and fam["cases"][0]["aliases"]:
                lines.append("- Aliases: " + json.dumps(fam["cases"][0]["aliases"], sort_keys=True))
            for case in fam["cases"]:
                if case["status"] != "exact_symbolic_equivalent":
                    lines.append("- Seed {}: {}{}".format(case["seed"], case["status"],
                      " — " + str(case["reason"]) if case["reason"] else ""))
            lines.append("")
    lines += ["## Safeguards", "",
      "- Aliases are used only for this post-hoc audit and are never written to original result files.",
      "- Invalid aliases are rejected; unsupported syntax remains not_assessable.",
      "- Generated formula defects are not repaired or overwritten by this script.", ""]
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    for p in protocols:
        print(p["protocol"], p["status_counts"])

if __name__ == "__main__":
    main()
