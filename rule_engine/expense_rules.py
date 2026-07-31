from typing import List, Dict, Any
from .models import Finding
from .config_loader import ConfigLoader
from .data_loader import DataLoader

class ExpenseRules:
    """
    Evaluates operating expenses, expense growth rates relative to revenue,
    and major cost category fluctuations against thresholds specified in config.json.
    """
    def __init__(self, config_loader: ConfigLoader, data_loader: DataLoader):
        self.config = config_loader
        self.data = data_loader

    def evaluate(self) -> List[Finding]:
        findings: List[Finding] = []
        dashboard_data = self.data.get_dashboard_data()
        
        # Retrieve thresholds from config
        exp_config = self.config.get("expense_rules", {})
        max_expense_growth = exp_config.get("max_expense_growth", 0.10) # e.g. 10% max growth
        max_opex_ratio = exp_config.get("max_opex_ratio", 0.70) # e.g. 70% opex/revenue

        sorted_years = sorted([yr for yr in dashboard_data.keys() if yr.isdigit()])
        if not sorted_years:
            return findings

        for i in range(1, len(sorted_years)):
            prev_yr = sorted_years[i - 1]
            curr_yr = sorted_years[i]
            
            curr_data = dashboard_data[curr_yr]
            kpis = curr_data.get("kpis", {})
            growth_trends = curr_data.get("datasets", {}).get("growth_trends", {})
            
            total_revenue = kpis.get("total_revenue", 0.0)
            total_expenses = kpis.get("total_expenses", 0.0)
            exp_growth = growth_trends.get("expenses", 0.0)
            rev_growth = growth_trends.get("revenue", 0.0)

            # Rule 1: Excessive Expense Growth vs Revenue Growth
            if exp_growth > max_expense_growth and exp_growth > rev_growth:
                findings.append(Finding(
                    module="Expense Rules",
                    finding=f"Accelerated Expense Growth ({exp_growth * 100:.1f}%) Exceeds Revenue Growth in FY{curr_yr}",
                    interpretation=f"Operating and total costs grew by {exp_growth * 100:.1f}%, outpacing top-line revenue expansion and eroding operating leverage.",
                    recommendation="Implement stringent cost control measures across overhead, administrative, and discretionary spending categories.",
                    severity="High",
                    confidence=0.90,
                    year=curr_yr,
                    metric_value=exp_growth,
                    threshold_value=max_expense_growth,
                    priority_score=8.5
                ))
            elif exp_growth > max_expense_growth:
                findings.append(Finding(
                    module="Expense Rules",
                    finding=f"High Expense Growth ({exp_growth * 100:.1f}%) in FY{curr_yr}",
                    interpretation=f"Expense growth of {exp_growth * 100:.1f}% exceeds the strategic ceiling of {max_expense_growth * 100:.1f}%.",
                    recommendation="Review department budgets and audit vendor expenditure for cost optimization opportunities.",
                    severity="Medium",
                    confidence=0.85,
                    year=curr_yr,
                    metric_value=exp_growth,
                    threshold_value=max_expense_growth,
                    priority_score=5.0
                ))
            else:
                findings.append(Finding(
                    module="Expense Rules",
                    finding=f"Controlled Expense Growth ({exp_growth * 100:.1f}%) in FY{curr_yr}",
                    interpretation=f"Expense expansion is well managed and aligned with strategic growth parameters.",
                    recommendation="Sustain current cost accountability and budget monitoring protocols.",
                    severity="Positive",
                    confidence=0.90,
                    year=curr_yr,
                    metric_value=exp_growth,
                    threshold_value=max_expense_growth,
                    priority_score=1.0
                ))

            # Rule 2: Expense to Revenue Ratio Check
            if total_revenue > 0:
                opex_ratio = total_expenses / total_revenue
                if opex_ratio > max_opex_ratio:
                    findings.append(Finding(
                        module="Expense Rules",
                        finding=f"High Cost-to-Revenue Ratio ({opex_ratio * 100:.1f}%) in FY{curr_yr}",
                        interpretation=f"Total expenditures consume {opex_ratio * 100:.1f}% of total revenues, leaving a narrow operational buffer.",
                        recommendation="Restructure fixed cost commitments and drive operational efficiencies to improve margin resilience.",
                        severity="High",
                        confidence=0.92,
                        year=curr_yr,
                        metric_value=opex_ratio,
                        threshold_value=max_opex_ratio,
                        priority_score=8.0
                    ))

        return findings