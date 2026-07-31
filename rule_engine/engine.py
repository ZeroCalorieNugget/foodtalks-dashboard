import json
from pathlib import Path
from typing import Dict, Any, List

from .config_loader import ConfigLoader
from .data_loader import DataLoader
from .revenue_rules import RevenueRules
from .profitability_rules import ProfitabilityRules
from .expense_rules import ExpenseRules
from .balance_sheet_rules import BalanceSheetRules
from .cash_flow_rules import CashFlowRules
from .alert_swot_rules import AlertSwotRules

class RuleEngineOrchestrator:
    """
    Orchestrates all financial rule evaluation modules, compiles findings,
    prioritizes alerts, and generates structured SWOT and executive summaries
    into insights.json.
    """
    def __init__(self, config_path: str = "config.json", dashboard_data_path: str = "dashboard_data.json", raw_data_path: str = "data.json"):
        self.config_loader = ConfigLoader(config_path)
        self.data_loader = DataLoader(dashboard_data_path, raw_data_path)
        
        # Instantiate rule evaluation modules
        self.revenue_rules = RevenueRules(self.config_loader, self.data_loader)
        self.profitability_rules = ProfitabilityRules(self.config_loader, self.data_loader)
        self.expense_rules = ExpenseRules(self.config_loader, self.data_loader)
        self.balance_sheet_rules = BalanceSheetRules(self.config_loader, self.data_loader)
        self.cash_flow_rules = CashFlowRules(self.config_loader, self.data_loader)
        self.alert_swot_rules = AlertSwotRules(self.config_loader)

    def run(self, output_json_path: str = "insights.json") -> Dict[str, Any]:
        all_findings: List[Any] = []
        
        # Execute all rule modules
        all_findings.extend(self.revenue_rules.evaluate())
        all_findings.extend(self.profitability_rules.evaluate())
        all_findings.extend(self.expense_rules.evaluate())
        all_findings.extend(self.balance_sheet_rules.evaluate())
        all_findings.extend(self.cash_flow_rules.evaluate())
        
        # Prioritize alerts and synthesize SWOT categories
        prioritized_alerts = self.alert_swot_rules.prioritize_alerts(all_findings)
        swot_summary = self.alert_swot_rules.generate_swot(all_findings)
        
        # Compile final insights output structure
        insights_payload = {
            "findings": [f.to_dict() for f in all_findings],
            "business_alerts": prioritized_alerts,
            "swot_summary": swot_summary
        }
        
        # Export to insights.json
        output_path = Path(output_json_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(insights_payload, f, indent=4, ensure_ascii=False)
            
        print(f"Success! Rule Engine executed successfully. Insights saved to {output_path}")
        return insights_payload

if __name__ == "__main__":
    engine = RuleEngineOrchestrator()
    engine.run()