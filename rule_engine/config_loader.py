import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigLoader:
    """
    Loads and manages external configuration parameters from config.json.
    Decouples business logic thresholds from Python source code.
    """
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found at {self.config_path}. Please complete Step 1 first."
            )
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a top-level configuration section or value."""
        return self._config.get(key, default)

    def get_threshold(self, category: str, threshold_name: str, default: Any = None) -> Any:
        """Retrieves a specific threshold or target value from a configuration category."""
        cat = self._config.get(category, {})
        if isinstance(cat, dict):
            return cat.get(threshold_name, default)
        return default