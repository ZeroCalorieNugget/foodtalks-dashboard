from typing import List, Dict, Any
from .models import Finding
from .config_loader import ConfigLoader
from .data_loader import DataLoader

class CashFlowRules:
    """
    Evaluates operating cash flow adequacy, cash conversion, cash burn runway,
    and cash flow stability against thresholds specified in config.json.
    """
    def __init__(self, config_loader: ConfigLoader, data_loader: DataLoader):
        self.config = config_loader
        self.data = data_loader

    def evaluate(self) -> List[Finding]:
        findings: List[Finding] = []
        dashboard_data = self.data.get_dashboard_data()
        
        # Retrieve thresholds from config
        cf_config = self.config.get("cash_flow_rules", {})
        min_cash_conversion = cf_config.get("min_cash_conversion", 0.5)
        max_cash_conversion = cf_config.get("max_cash_conversion", 1.5)
        critical_cash_burn_months = cf_config.get("critical_cash_burn_months", 6.0)

        sorted_years = sorted([yr for yr in dashboard_data.keys() if yr.isdigit()])
        if not sorted_years:
            return findings

        for yr in sorted_years:
            curr_data = dashboard_data[yr]
            kpis = curr_data.get("kpis", {})
            
            cash_conversion = kpis.get("cash_conversion", 1.0)
            cash_burn = kpis.get("cash_burn", 24.0)

            # Rule 1: Cash Conversion Ratio Check (Earnings Quality)
            if cash_conversion < min_cash_conversion:
                findings.append(Finding(
                    module="Cash Flow Rules",
                    finding=f"Low Cash Conversion Ratio ({cash_conversion:.2f}) in FY{yr}",
                    interpretation=f"Operating cash flow represents only {cash_conversion * 100:.1f}% of net profit, signaling potential earnings quality issues or delayed receivables realization.",
                    recommendation="Audit working capital components, accelerate receivables collection, and examine non-cash revenue accruals.",
                    severity="High",
                    confidence=0.90,
                    year=yr,
                    metric_value=cash_conversion,
                    threshold_value=min_cash_conversion,
                    priority_score=8.5
                ))
            elif cash_conversion > max_cash_conversion:
                findings.append(Finding(
                    module="Cash Flow Rules",
                    finding=f"High Cash Conversion Ratio ({cash_conversion:.2f}) in FY{yr}",
                    interpretation=f"Operating cash generation ({cash_conversion * 100:.1f}% of net profit) significantly exceeds net earnings, reflecting strong cash realization.",
                    recommendation="Deploy excess operating cash toward strategic growth investments or debt reduction.",
                    severity="Positive",
                    confidence=0.88,
                    year=yr,
                    metric_value=cash_conversion,
                    threshold_value=max_cash_conversion,
                    priority_score=1.0
                ))
            else:
                findings.append(Finding(
                    module="Cash Flow Rules",
                    finding=f"Stable Cash Conversion ({cash_conversion:.2f}) in FY{yr}",
                    interpretation=f"Cash flow from operations aligns healthily with net profit within the target stability band ({min_cash_conversion}–{max_cash_conversion}).",
                    recommendation="Maintain rigorous cash collection schedules and working capital discipline.",
                    severity="Positive",
                    confidence=0.90,
                    year=yr,
                    metric_value=cash_conversion,
                    threshold_value=min_cash_conversion,
                    priority_score=1.0
                ))

            # Rule 2: Cash Burn / Runway Check
            if cash_burn < critical_cash_burn_months and cash_burn > 0:
                findings.append(Finding(
                    module="Cash Flow Rules",
                    finding=f"Critical Cash Runway Risk: {cash_burn:.1f} Months Remaining in FY{yr}",
                    interpretation=f"Available cash reserves provide less than {critical_cash_burn_months} months of operational runway based on current cash burn rates.",
                    recommendation="Execute emergency cash preservation protocols, defer non-essential expenditures, and secure bridge liquidity immediately.",
                    severity="Critical",
                    confidence=0.96,
                    year=yr,
                    metric_value=cash_burn,
                    threshold_value=critical_cash_burn_months,
                    priority_score=10.0
                ))

        return findings