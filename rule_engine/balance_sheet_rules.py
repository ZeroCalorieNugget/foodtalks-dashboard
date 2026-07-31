from typing import List, Dict, Any
from .models import Finding
from .config_loader import ConfigLoader
from .data_loader import DataLoader

class BalanceSheetRules:
    """
    Evaluates short-term liquidity, working capital health, and solvency ratios 
    (Current Ratio, Cash Ratio) against critical risk thresholds specified in config.json.
    """
    def __init__(self, config_loader: ConfigLoader, data_loader: DataLoader):
        self.config = config_loader
        self.data = data_loader

    def evaluate(self) -> List[Finding]:
        findings: List[Finding] = []
        dashboard_data = self.data.get_dashboard_data()
        
        # Retrieve thresholds from config
        bs_config = self.config.get("balance_sheet_rules", {})
        min_current_ratio = bs_config.get("min_current_ratio", 1.0)
        critical_current_ratio = bs_config.get("critical_current_ratio", 0.8)
        min_cash_ratio = bs_config.get("min_cash_ratio", 0.5)

        sorted_years = sorted([yr for yr in dashboard_data.keys() if yr.isdigit()])
        if not sorted_years:
            return findings

        for yr in sorted_years:
            curr_data = dashboard_data[yr]
            kpis = curr_data.get("kpis", {})
            
            current_ratio = kpis.get("current_ratio", 1.5)
            cash_ratio = kpis.get("cash_ratio", 0.8)

            # Rule 1: Current Ratio Liquidity Risk
            if current_ratio < critical_current_ratio:
                findings.append(Finding(
                    module="Balance Sheet Rules",
                    finding=f"Severe Liquidity Risk: Low Current Ratio ({current_ratio:.2f}) in FY{yr}",
                    interpretation=f"Current assets fall significantly short of short-term liabilities (critical threshold: {critical_current_ratio}), indicating imminent short-term solvency pressure.",
                    recommendation="Accelerate receivables collection, defer non-essential capital expenditures, or secure short-term credit facilities.",
                    severity="Critical",
                    confidence=0.95,
                    year=yr,
                    metric_value=current_ratio,
                    threshold_value=critical_current_ratio,
                    priority_score=9.8
                ))
            elif current_ratio < min_current_ratio:
                findings.append(Finding(
                    module="Balance Sheet Rules",
                    finding=f"Sub-optimal Current Ratio ({current_ratio:.2f}) in FY{yr}",
                    interpretation=f"Current ratio of {current_ratio:.2f} is below the safe benchmark of {min_current_ratio}, indicating tight working capital management.",
                    recommendation="Optimize inventory turnover and tighten credit terms for customers to improve liquid buffers.",
                    severity="High",
                    confidence=0.90,
                    year=yr,
                    metric_value=current_ratio,
                    threshold_value=min_current_ratio,
                    priority_score=7.2
                ))
            else:
                findings.append(Finding(
                    module="Balance Sheet Rules",
                    finding=f"Healthy Liquidity Buffer: Current Ratio ({current_ratio:.2f}) in FY{yr}",
                    interpretation=f"Current assets adequately cover short-term obligations, maintaining robust operational liquidity.",
                    recommendation="Maintain balanced working capital policies and review idle cash deployment.",
                    severity="Positive",
                    confidence=0.90,
                    year=yr,
                    metric_value=current_ratio,
                    threshold_value=min_current_ratio,
                    priority_score=1.0
                ))

            # Rule 2: Cash Ratio Check
            if cash_ratio < min_cash_ratio:
                findings.append(Finding(
                    module="Balance Sheet Rules",
                    finding=f"Low Cash Ratio ({cash_ratio:.2f}) in FY{yr}",
                    interpretation=f"Cash and cash equivalents provide limited immediate coverage for short-term liabilities relative to benchmark ({min_cash_ratio}).",
                    recommendation="Build cash reserves by prioritizing high-margin cash sales and managing accounts payable outflows.",
                    severity="Medium",
                    confidence=0.88,
                    year=yr,
                    metric_value=cash_ratio,
                    threshold_value=min_cash_ratio,
                    priority_score=6.0
                ))

        return findings