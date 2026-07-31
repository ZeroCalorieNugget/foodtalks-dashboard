from rule_engine.engine import RuleEngineOrchestrator

def main():
    """
    Top-level entry point for executing the Financial Dashboard Rule Engine.
    Loads configuration, reads processed dashboard data and raw financial records,
    evaluates all diagnostic rules, prioritizes alerts, and exports insights.json.
    """
    print("--- Starting Financial Diagnostic Rule Engine ---")
    
    try:
        orchestrator = RuleEngineOrchestrator(
            config_path="config.json",
            dashboard_data_path="dashboard_data.json",
            raw_data_path="data.json"
        )
        orchestrator.run(output_json_path="insights.json")
        print("--- Rule Engine Execution Completed Successfully ---")
    except Exception as e:
        print(f"Error executing Rule Engine: {e}")
        raise

if __name__ == "__main__":
    main()