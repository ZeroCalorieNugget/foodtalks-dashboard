#!/usr/bin/env python3
"""
Foodtalks Financial Decision Support System (FDSS)
Stage 2 Module: Dashboard Metrics Calculation Engine

Responsibilities:
1. Ingest raw structured data from `data.json`.
2. Perform robust dual-key inspection on Balance Sheet items (checking both `accounting item`
   and `category 01` tags) to correctly accumulate current assets, current liabilities, and cash balances.
3. Compute core KPIs, liquidity ratios (Current Ratio, Cash Ratio), burn rate, 
   cash conversion, and category-level YoY growth trends.
4. Export calculated metrics into `dashboard_data.json` for consumption by the Rule Engine
   and Frontend Dashboard.
"""

import json
import os
from pathlib import Path

INPUT_JSON_PATH = Path("data.json")
OUTPUT_JSON_PATH = Path("dashboard_data.json")
CONFIG_PATH = Path("config.json")


def get_float_val(row: dict, year: str) -> float:
    """Safely extract and convert year values to float, handling strings with currency symbols or commas."""
    try:
        val = row.get(year, 0.0)
        if val is None or val == "" or val == "—":
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        # Strip currency symbols and commas if present in raw string
        clean_str = str(val).replace("$", "").replace(",", "").strip()
        return float(clean_str) if clean_str else 0.0
    except (ValueError, TypeError):
        return 0.0


def calculate_dashboard_metrics():
    if not INPUT_JSON_PATH.exists():
        print(f"[Error] Input file '{INPUT_JSON_PATH}' not found.")
        return

    with open(INPUT_JSON_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    is_rows = raw_data.get("income_statement", {}).get("table_rows", [])
    bs_rows = raw_data.get("balance_sheet", {}).get("table_rows", [])
    cf_rows = raw_data.get("cash_flow_statement", {}).get("table_rows", [])

    # Extract all 4-digit years available in dataset
    years_set = set()
    for dataset in [is_rows, bs_rows, cf_rows]:
        for r in dataset:
            for k in r.keys():
                k_clean = str(k).strip()
                if len(k_clean) == 4 and k_clean.isdigit():
                    years_set.add(k_clean)

    sorted_years = sorted(list(years_set))
    if not sorted_years:
        print("[Error] No valid year columns found in data.json.")
        return

    dashboard_data = {}

    # Separate Income Statement rows
    rev_rows = [
        r for r in is_rows
        if str(r.get("accounting item", "")).strip().lower() == "trading income"
        or str(r.get("category 01", "")).strip().lower() == "revenue"
    ]
    cos_rows = [
        r for r in is_rows
        if str(r.get("accounting item", "")).strip().lower() == "cost of sales"
        or str(r.get("category 01", "")).strip().lower() == "cost"
    ]
    opex_rows = [
        r for r in is_rows
        if r not in rev_rows and r not in cos_rows
    ]

    for idx, yr in enumerate(sorted_years):
        # 1. Income Statement Metrics
        revenue = sum(get_float_val(r, yr) for r in rev_rows)
        cos = sum(get_float_val(r, yr) for r in cos_rows)
        gp = revenue - cos
        gpm = (gp / revenue) if revenue != 0 else 0.0

        opex = sum(get_float_val(r, yr) for r in opex_rows)
        net_profit = revenue - cos - opex
        npm = (net_profit / revenue) if revenue != 0 else 0.0

        # 2. Balance Sheet Dual-Key Aggregation
        ca = 0.0
        cl = 0.0
        cash = 0.0

        for r in bs_rows:
            item = str(r.get("accounting item", "")).strip().lower()
            cat01 = str(r.get("category 01", "")).strip().lower()
            val = get_float_val(r, yr)

            # Skip summary total rows if detailed category tags exist
            if item.startswith("total ") and cat01 not in ["none", ""]:
                continue

            # Independent Dual-Key Check for Current Assets
            if (
                "current asset" in item
                or "current asset" in cat01
                or cat01 in ["current assets", "ca"]
            ):
                ca += val

            # Independent Dual-Key Check for Current Liabilities
            if (
                "current liabilit" in item
                or "current liabilit" in cat01
                or cat01 in ["current liabilities", "cl"]
            ):
                cl += val

            # Independent Dual-Key Check for Cash & Cash Equivalents
            if (
                "cash" in item
                or "cash" in cat01
                or cat01 in ["cash", "cash & cash equivalents"]
            ):
                cash += val

        # 3. Cash Flow Statement Metrics
        ocf = 0.0
        cfi = 0.0
        cff = 0.0
        net_cf = 0.0

        for r in cf_rows:
            item = str(r.get("accounting item", "")).strip().lower()
            val = get_float_val(r, yr)
            if "operating cash flow" in item or "cfo" in item:
                ocf = val
            elif "investing cash flow" in item or "cfi" in item:
                cfi = val
            elif "financing cash flow" in item or "cff" in item:
                cff = val
            elif "net increase in cash" in item or "net cash flow" in item:
                net_cf = val

        # 4. Solvency & Liquidity Ratios
        current_ratio = round(ca / cl, 2) if cl != 0 else 0.0
        cash_ratio = round(cash / cl, 2) if cl != 0 else 0.0
        
        monthly_burn = net_cf / 12.0 if net_cf != 0 else (ocf / 12.0 if ocf != 0 else 0.0)
        cash_burn_months = round(abs(cash / monthly_burn), 1) if (cash != 0 and monthly_burn != 0) else 0.0
        cash_conversion = round(ocf / net_profit, 2) if net_profit != 0 else 0.0

        # 5. Expense Category Breakdowns
        cat01_map = {}
        cat02_map = {}
        exp_comp = {}

        for r in is_rows:
            c01 = str(r.get("category 01", "")).strip().lower()
            c02 = str(r.get("category 02", "")).strip().lower()
            breakup = str(r.get("accounting break_up item", "")).strip()
            val = get_float_val(r, yr)

            if c01 and c01 != "none":
                cat01_map[c01] = cat01_map.get(c01, 0.0) + val
            if c02 and c02 != "none":
                cat02_map[c02] = cat02_map.get(c02, 0.0) + val
                if c02 not in exp_comp:
                    exp_comp[c02] = {}
                if breakup:
                    exp_comp[c02][breakup] = exp_comp[c02].get(breakup, 0.0) + val

        exp_breakdown = {k: v for k, v in cat02_map.items() if "revenue" not in k}

        # Assemble KPI object
        kpis = {
            "total_revenue": round(revenue, 2),
            "gross_profit_margin": round(gpm, 4),
            "net_profit_margin": round(npm, 4),
            "operating_cash_flow": round(ocf, 2),
            "current_ratio": current_ratio,
            "cash_ratio": cash_ratio,
            "cash_burn_months": cash_burn_months,
            "cash_conversion": cash_conversion,
        }

        rev_alloc = {"revenue": round(revenue, 2), "profit": round(net_profit, 2)}
        rev_alloc.update({k: round(v, 2) for k, v in cat01_map.items()})

        datasets = {
            "revenue_allocation": rev_alloc,
            "margin_compression": {
                "gross_profit_margin": round(gpm, 4),
                "net_profit_margin": round(npm, 4),
            },
            "expenditure_breakdown": {k: round(v, 2) for k, v in exp_breakdown.items()},
            "cash_flow_summary": {"cfo": round(ocf, 2), "cfi": round(cfi, 2), "cff": round(cff, 2)},
            "expenditure_components": exp_comp,
        }

        # 6. Year-over-Year Growth Trends
        growth_trends = {}
        if idx == 0:
            growth_trends["revenue"] = 0.0
            growth_trends["categories"] = {k: 0.0 for k in exp_breakdown.keys()}
        else:
            prev_yr = sorted_years[idx - 1]
            prev_rev = dashboard_data[prev_yr]["kpis"]["total_revenue"]
            growth_trends["revenue"] = (
                round((revenue - prev_rev) / prev_rev, 4) if prev_rev != 0 else 0.0
            )

            cat_growths = {}
            prev_exp = dashboard_data[prev_yr]["datasets"]["expenditure_breakdown"]
            for cat02, val in exp_breakdown.items():
                prev_val = prev_exp.get(cat02, 0.0)
                previous_cost = abs(prev_val)
                current_cost = abs(val)
                cat_growths[cat02] = (
                    round((current_cost - previous_cost) / previous_cost, 4)
                    if previous_cost != 0
                    else 0.0
                )
            growth_trends["categories"] = cat_growths

        datasets["growth_trends"] = growth_trends
        dashboard_data[yr] = {"kpis": kpis, "datasets": datasets}

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=4, ensure_ascii=False)

    print(f"Success! Corrected dashboard metrics exported to {OUTPUT_JSON_PATH}")


if __name__ == "__main__":
    calculate_dashboard_metrics()
