import json
from pathlib import Path
from typing import Dict, Any

class DataLoader:
    """
    Loads pre-calculated dashboard metrics (dashboard_data.json) 
    and raw hierarchical financial statement records (data.json).
    """
    def __init__(self, dashboard_data_path: str = "dashboard_data.json", raw_data_path: str = "data.json"):
        self.dashboard_data_path = Path(dashboard_data_path)
        self.raw_data_path = Path(raw_data_path)
        self.dashboard_data: Dict[str, Any] = {}
        self.raw_data: Dict[str, Any] = {}
        self.load_data()

    def load_data(self) -> None:
        if self.dashboard_data_path.exists():
            with open(self.dashboard_data_path, "r", encoding="utf-8") as f:
                self.dashboard_data = json.load(f)
        else:
            raise FileNotFoundError(
                f"Dashboard data file not found at {self.dashboard_data_path}. Please complete pipeline calculation first."
            )

        if self.raw_data_path.exists():
            with open(self.raw_data_path, "r", encoding="utf-8") as f:
                self.raw_data = json.load(f)
        else:
            raise FileNotFoundError(
                f"Raw data file not found at {self.raw_data_path}. Please complete data extraction first."
            )

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Returns the processed dashboard metrics and dataset dictionary by year."""
        return self.dashboard_data

    def get_raw_data(self) -> Dict[str, Any]:
        """Returns the raw hierarchical financial statement records."""
        return self.raw_data