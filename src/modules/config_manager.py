import json
from pathlib import Path
from typing import Any, Dict


class ConfigManager:
    def __init__(self, config_path: str = 'config/config.json'):
        self.config_path = Path(config_path)
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if self.config_path.exists():
            with self.config_path.open('r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            raise FileNotFoundError(f"Config not found: {self.config_path}")

    def get(self, section: str, key: str, default: Any = None) -> Any:
        return self.data.get(section, {}).get(key, default)
