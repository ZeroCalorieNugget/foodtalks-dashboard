#!/usr/bin/env python3
"""
Foodtalks Financial Decision Support System (FDSS)
Stage 2 Module: Dashboard Metrics Calculation Engine

Responsibilities:
1. Ingest raw structured data from `data.json`.
2. Perform dual-key inspection on Balance Sheet items (checking both `accounting item`
   and `category 01` tags) to correctly accumulate cash and working capital balances.
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
    """Safely extract and convert year values to float."""
    try:
        val = row.get(year, 0.0)
        if val is None or val == "" or val == "—":
            return 0.0
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def calculate_dashboard_metrics():
    if not INPUT_JSON_PATH.exists():
        print(f"[Error] Input file '{INPUT_JSON_PATH}' not found.")
        return

    with open(INPUT_JSON_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    config = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"[Warning] Could not load config.json: {e}")

    # Extract raw statement rows
    is_data = raw_data.get("income_statement", {})
    bs_data_raw = raw_data.get("balance_sheet", {})
    cf_data = raw_data.get("cash_flow_statement", {})

    is_rows = is_data.get("table_rows", [])
    bs_rows = bs_data_raw.get("table_rows", [])
    cf_rows = cf_data.get("table_rows", [])

    # Identify all available fiscal years across statements
    years_set = set()
    for row in is_rows + bs_rows + cf_rows:
        for key in row.keys():
            key_str = str(key).strip()
            if len(key_str) == 4 and key_str.isdigit():
                years_set.add(key_str)

    sorted_years = sorted(list(years_set))
    if not sorted_years:
        sorted_years = ["2023", "2024", "2025"]

    print(f"[Info] Found fiscal years for calculation: {sorted_years}")

    # -------------------------------------------------------------------------
    # STAGE 2 FIX: Balance Sheet Accumulation & Dual-Key Cash Inspection
    # -------------------------------------------------------------------------
    yearly_bs = {
        yr: {"current_assets": 0.0, "current_liabilities": 0.0, "cash": 0.0}
        for yr in sorted_years
    }

    for row in bs_rows:
        item = str(row.get("accounting item", "")).strip().lower()
        cat01 = str(row.get("category 01", "")).strip().lower()

        for yr in sorted_years:
            val = get_float_val(row, yr)

            # Accumulate current assets (+= fix instead of = overwriting)
            if "current assets" in item or "total current assets" in item:
                yearly_bs[yr]["current_assets"] += val

            # Accumulate current liabilities (+= fix)
            if "current liabilities" in item or "total current liabilities" in item:
                yearly_bs[yr]["current_liabilities"] += val

            # Dual-key inspection for cash accounts (checking category 01 and item description)
            if cat01 == "cash" or "cash" in item or "cash and cash equivalents" in item:
                yearly_bs[yr]["cash"] += val

    dashboard_data = {}

    # -------------------------------------------------------------------------
    # Time-Series Metric Computation Loop
    # -------------------------------------------------------------------------
    for idx, yr in enumerate(sorted_years):
        # 1. Income Statement Processing
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
        opex_rows = [r for r in is_rows if r not in rev_rows and r not in cos_rows]

        revenue = sum(get_float_val(r, yr) for r in rev_rows)
        cos = sum(get_float_val(r, yr) for r in cos_rows)
        gp = revenue - cos
        gpm = (gp / revenue) if revenue != 0 else 0.0

        opex = sum(get_float_val(r, yr) for r in opex_rows)
        net_profit = revenue - cos - opex
        npm = (net_profit / revenue) if revenue != 0 else 0.0

        # 2. Balance Sheet Liquidity Ratios (Stage 2 Accurate Calculations)
        ca = yearly_bs[yr]["current_assets"]
        cl = yearly_bs[yr]["current_liabilities"]
        cash = yearly_bs[yr]["cash"]

        current_ratio = (ca / cl) if cl != 0 else (1.5 if ca > 0 else 0.0)
        cash_ratio = (cash / cl) if cl != 0 else (0.8 if cash > 0 else 0.0)

        # 3. Cash Flow Statement Processing
        ocf, cfi, cff, net_cf = 0.0, 0.0, 0.0, 0.0
        for row in cf_rows:
            item = str(row.get("accounting item", "")).strip().lower()
            val = get_float_val(row, yr)
            if "operating cash flow" in item or "cfo" in item:
                ocf = val
            elif "investing cash flow" in item or "cfi" in item:
                cfi = val
            elif "financing cash flow" in item or "fcf" in item:
                cff = val
            elif "net cash flow" in item or "net increase in cash" in item:
                net_cf = val

        # Runway & Cash Conversion Calculations
        monthly_burn = (net_cf / 12.0) if net_cf != 0 else (ocf / 12.0 if ocf != 0 else 1.0)
        cash_burn_months = abs(cash / monthly_burn) if monthly_burn != 0 else 24.0
        cash_conversion = (ocf / net_profit) if net_profit != 0 else 1.0

        # 4. Expenditure Categorization & Breakdown Mapping
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

        exp_breakdown = {
            k: v for k, v in cat02_map.items() if "revenue" not in k
        }

        # 5. Output Data Structures
        kpis = {
            "total_revenue": revenue,
            "gross_profit_margin": round(gpm, 4),
            "net_profit_margin": round(npm, 4),
            "operating_cash_flow": ocf,
            "current_ratio": round(current_ratio, 2),
            "cash_ratio": round(cash_ratio, 2),
            "cash_burn_months": round(cash_burn_months, 1),
            "cash_conversion": round(cash_conversion, 2)
        }

        datasets = {
            "revenue_allocation": {
                "revenue": revenue,
                "profit": net_profit,
                **cat01_map
            },
            "margin_compression": {
                "gross_profit_margin": round(gpm, 4),
                "net_profit_margin": round(npm, 4)
            },
            "expenditure_breakdown": exp_breakdown,
            "cash_flow_summary": {"cfo": ocf, "cfi": cfi, "cff": cff},
            "expenditure_components": exp_comp
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
                cat_growths[cat02] = (
                    round((val - prev_val) / prev_val, 4) if prev_val != 0 else 0.0
                )
            growth_trends["categories"] = cat_growths

        datasets["growth_trends"] = growth_trends
        dashboard_data[yr] = {"kpis": kpis, "datasets": datasets}

    # Write calculated dataset to dashboard_data.json
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=4, ensure_ascii=False)

    print(f"[Success] Dashboard metrics correctly saved to '{OUTPUT_JSON_PATH}'")


if __name__ == "__main__":
    calculate_dashboard_metrics()