"""
Foodtalks Financial Decision Support System (FDSS)
Rule Engine: Alert Prioritization & Option C Strategic SWOT Synthesizer
"""

from typing import List, Dict, Any
from .models import Finding
from .config_loader import ConfigLoader

class AlertSwotRules:
    """
    Aggregates findings from all rule modules, prioritizes urgent business alerts,
    and synthesizes findings into a classical, non-redundant SWOT Summary Matrix
    aligned with Option C (Current-Year Strategic Snapshot + Multi-Year Context).
    """
    def __init__(self, config_loader: ConfigLoader):
        self.config = config_loader

    def prioritize_alerts(self, findings: List[Finding]) -> List[Dict[str, Any]]:
        """
        Sorts and prioritizes non-positive findings into Executive Business Alerts.
        Serves as an Urgency Filter for High and Critical severity risks.
        """
        severity_weights = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Positive": 0}
        
        sorted_findings = sorted(
            findings,
            key=lambda f: (severity_weights.get(f.severity, 0), getattr(f, "priority_score", 1.0)),
            reverse=True
        )

        alerts = []
        for f in sorted_findings:
            if f.severity == "Positive":
                continue  # Positive findings are synthesized into Strengths/Opportunities
            
            alerts.append({
                "level": f.severity,  # Critical, High, Medium, Low
                "module": f.module,
                "title": f.finding,
                "interpretation": f.interpretation,
                "recommendation": f.recommendation,
                "year": f.year,
                "priority_score": getattr(f, "priority_score", 1.0)
            })
        return alerts

    def generate_swot(self, findings: List[Finding]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Synthesizes findings into classical SWOT categories (Strengths, Weaknesses, Opportunities, Threats)
        aligned with Option C (Current-Year Strategic Snapshot + Embedded Multi-Year Context).
        
        Methodological Distinctions:
        - Strengths: Internal core competencies & profitability/liquidity buffers.
        - Weaknesses: Internal operational friction, cost structure pressure, or OpEx leakage.
        - Opportunities: Forward-looking growth drivers, multi-year expansion, cash conversion momentum.
        - Threats: Solvency risks, short runway (<6 mo), persistent multi-year margin contraction.
        """
        swot = {
            "Strengths": [],
            "Weaknesses": [],
            "Opportunities": [],
            "Threats": []
        }

        for f in findings:
            item = {
                "module": f.module,
                "text": f.finding,
                "details": f.interpretation,
                "year": f.year
            }

            text_lower = f.finding.lower()
            module_lower = f.module.lower()
            interp_lower = (f.interpretation or "").lower()

            if f.severity == "Positive":
                # Internal capability = Strength; Forward trajectory / growth driver = Opportunity
                is_opportunity = any(k in module_lower or k in text_lower or k in interp_lower for k in [
                    "expansion", "growth", "opportunity", "cash flow", "cfo", "conversion", "efficiency", "trajectory", "multi-year"
                ]) and not ("gross margin" in text_lower or "net profit margin" in text_lower)

                if is_opportunity:
                    swot["Opportunities"].append(item)
                else:
                    swot["Strengths"].append(item)

            else:
                # Non-positive findings (Critical, High, Medium, Low)
                # Solvency / Short Runway / Persistent Multi-Year Contraction = Threats
                # Internal cost pressure / margin leakages = Weaknesses
                is_threat = any(k in module_lower or k in text_lower or k in interp_lower for k in [
                    "balance sheet", "solvency", "cash burn", "debt", "runway", "persistent",
                    "consecutive", "liquidity shortfall", "macroeconomic", "supplier"
                ])

                if is_threat:
                    swot["Threats"].append(item)
                else:
                    swot["Weaknesses"].append(item)

        return swot