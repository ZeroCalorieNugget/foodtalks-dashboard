from typing import List, Dict, Any
from .models import Finding
from .config_loader import ConfigLoader
from .data_loader import DataLoader

class RevenueRules:
    """
    Evaluates revenue performance, year-over-year growth trends, and target variances
    against thresholds specified in config.json.
    """
    def __init__(self, config_loader: ConfigLoader, data_loader: DataLoader):
        self.config = config_loader
        self.data = data_loader

    def evaluate(self) -> List[Finding]:
        findings: List[Finding] = []
        dashboard_data = self.data.get_dashboard_data()
        
        # Retrieve thresholds from config
        rev_config = self.config.get("revenue_rules", {})
        min_growth_target = rev_config.get("min_growth_target", 0.05) # e.g. 5% growth target
        critical_decline_threshold = rev_config.get("critical_decline_threshold", -0.05) # -5% decline

        sorted_years = sorted([yr for yr in dashboard_data.keys() if yr.isdigit()])
        if not sorted_years:
            return findings

        # Evaluate year-over-year trends
        for i in range(1, len(sorted_years)):
            prev_yr = sorted_years[i - 1]
            curr_yr = sorted_years[i]
            
            curr_data = dashboard_data[curr_yr]
            kpis = curr_data.get("kpis", {})
            growth_trends = curr_data.get("datasets", {}).get("growth_trends", {})
            
            rev_growth = growth_trends.get("revenue", 0.0)
            total_revenue = kpis.get("total_revenue", 0.0)

            # Rule 1: Revenue Decline / Negative Growth
            if rev_growth < critical_decline_threshold:
                findings.append(Finding(
                    module="Revenue Rules",
                    finding=f"Severe Revenue Decline ({rev_growth * 100:.1f}%) in FY{curr_yr}",
                    interpretation=f"Revenue fell by {abs(rev_growth * 100):.1f}% compared to FY{prev_yr}, indicating weakening commercial momentum or market demand.",
                    recommendation="Review customer acquisition strategies, pricing power, and pipeline conversion rates immediately.",
                    severity="Critical",
                    confidence=0.95,
                    year=curr_yr,
                    metric_value=rev_growth,
                    threshold_value=critical_decline_threshold,
                    priority_score=9.5
                ))
            elif rev_growth < 0:
                findings.append(Finding(
                    module="Revenue Rules",
                    finding=f"Mild Revenue Contraction ({rev_growth * 100:.1f}%) in FY{curr_yr}",
                    interpretation=f"Top-line revenue contracted slightly in FY{curr_yr} relative to FY{prev_yr}.",
                    recommendation="Monitor sales pipeline velocity and evaluate promotional effectiveness.",
                    severity="High",
                    confidence=0.90,
                    year=curr_yr,
                    metric_value=rev_growth,
                    threshold_value=0.0,
                    priority_score=7.0
                ))
            elif rev_growth < min_growth_target:
                findings.append(Finding(
                    module="Revenue Rules",
                    finding=f"Sub-target Revenue Growth ({rev_growth * 100:.1f}%) in FY{curr_yr}",
                    interpretation=f"Growth rate of {rev_growth * 100:.1f}% is below the minimum strategic benchmark of {min_growth_target * 100:.1f}% for FY{curr_yr}.",
                    recommendation="Optimize go-to-market channels and explore upselling opportunities within existing client accounts.",
                    severity="Medium",
                    confidence=0.85,
                    year=curr_yr,
                    metric_value=rev_growth,
                    threshold_value=min_growth_target,
                    priority_score=4.5
                ))
            else:
                findings.append(Finding(
                    module="Revenue Rules",
                    finding=f"Healthy Revenue Growth ({rev_growth * 100:.1f}%) in FY{curr_yr}",
                    interpretation=f"Top-line expansion successfully meets or exceeds the target benchmark of {min_growth_target * 100:.1f}%.",
                    recommendation="Maintain current sales cadence and scale successful revenue-generating campaigns.",
                    severity="Positive",
                    confidence=0.90,
                    year=curr_yr,
                    metric_value=rev_growth,
                    threshold_value=min_growth_target,
                    priority_score=1.0
                ))

        return findings