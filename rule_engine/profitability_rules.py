from typing import List, Dict, Any
from .models import Finding
from .config_loader import ConfigLoader
from .data_loader import DataLoader

class ProfitabilityRules:
    """
    Evaluates profitability margins (Gross Margin, Operating Margin, Net Profit Margin)
    against benchmarks and critical risk thresholds specified in config.json.
    """
    def __init__(self, config_loader: ConfigLoader, data_loader: DataLoader):
        self.config = config_loader
        self.data = data_loader

    def evaluate(self) -> List[Finding]:
        findings: List[Finding] = []
        dashboard_data = self.data.get_dashboard_data()
        
        # Retrieve thresholds from config
        prof_config = self.config.get("profitability_rules", {})
        min_gross_margin = prof_config.get("min_gross_margin", 0.30)
        min_net_margin = prof_config.get("min_net_margin", 0.05)
        critical_net_margin = prof_config.get("critical_net_margin", 0.0)

        sorted_years = sorted([yr for yr in dashboard_data.keys() if yr.isdigit()])
        if not sorted_years:
            return findings

        for yr in sorted_years:
            curr_data = dashboard_data[yr]
            kpis = curr_data.get("kpis", {})
            
            # Fix: Retrieve correct key 'gross_profit_margin' exported by calculate_dashboard.ipynb
            gross_margin = kpis.get("gross_profit_margin", kpis.get("gross_margin", 0.0))
            net_margin = kpis.get("net_profit_margin", 0.0)
            operating_margin = kpis.get("operating_margin", 0.0)

            # Rule 1: Net Profit Margin Critical Check
            if net_margin < critical_net_margin:
                findings.append(Finding(
                    module="Profitability Rules",
                    finding=f"Net Loss / Negative Profit Margin ({net_margin * 100:.1f}%) in FY{yr}",
                    interpretation=f"The firm experienced a net loss or zero profitability in FY{yr}, indicating structural cost pressures or insufficient pricing.",
                    recommendation="Conduct an immediate cost audit, streamline operational overhead, and re-evaluate pricing structures.",
                    severity="Critical",
                    confidence=0.95,
                    year=yr,
                    metric_value=net_margin,
                    threshold_value=critical_net_margin,
                    priority_score=10.0
                ))
            elif net_margin < min_net_margin:
                findings.append(Finding(
                    module="Profitability Rules",
                    finding=f"Low Net Profit Margin ({net_margin * 100:.1f}%) in FY{yr}",
                    interpretation=f"Net profit margin for FY{yr} falls below the target benchmark of {min_net_margin * 100:.1f}%.",
                    recommendation="Identify margin leakages across operating expense categories and improve cost efficiencies.",
                    severity="High",
                    confidence=0.90,
                    year=yr,
                    metric_value=net_margin,
                    threshold_value=min_net_margin,
                    priority_score=7.5
                ))
            else:
                findings.append(Finding(
                    module="Profitability Rules",
                    finding=f"Healthy Net Profit Margin ({net_margin * 100:.1f}%) in FY{yr}",
                    interpretation=f"Net profit margin comfortably meets or exceeds the baseline target of {min_net_margin * 100:.1f}%.",
                    recommendation="Sustain cost discipline and evaluate reinvestment opportunities into growth initiatives.",
                    severity="Positive",
                    confidence=0.90,
                    year=yr,
                    metric_value=net_margin,
                    threshold_value=min_net_margin,
                    priority_score=1.0
                ))

            # Rule 2: Gross Margin Check
            if gross_margin < min_gross_margin:
                findings.append(Finding(
                    module="Profitability Rules",
                    finding=f"Sub-optimal Gross Margin ({gross_margin * 100:.1f}%) in FY{yr}",
                    interpretation=f"Gross margin of {gross_margin * 100:.1f}% is below the target threshold of {min_gross_margin * 100:.1f}%, reflecting high direct costs or COGS pressure.",
                    recommendation="Review supplier contracts, material input costs, and production efficiencies.",
                    severity="High",
                    confidence=0.88,
                    year=yr,
                    metric_value=gross_margin,
                    threshold_value=min_gross_margin,
                    priority_score=8.0
                ))
            else:
                findings.append(Finding(
                    module="Profitability Rules",
                    finding=f"Healthy Gross Margin ({gross_margin * 100:.1f}%) in FY{yr}",
                    interpretation=f"Gross margin of {gross_margin * 100:.1f}% meets or exceeds the baseline benchmark of {min_gross_margin * 100:.1f}%.",
                    recommendation="Maintain pricing power and supplier cost controls.",
                    severity="Positive",
                    confidence=0.88,
                    year=yr,
                    metric_value=gross_margin,
                    threshold_value=min_gross_margin,
                    priority_score=1.0
                ))

        return findings