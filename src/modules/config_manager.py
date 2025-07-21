import json
import os
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


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
        # 먼저 config.json에서 값 확인
        config_value = self.data.get(section, {}).get(key, default)
        
        # video_folder_path의 경우 환경변수 FOLDER_PATH를 우선 사용
        if section == 'general' and key == 'video_folder_path':
            env_folder_path = os.getenv('FOLDER_PATH')
            if env_folder_path:
                return env_folder_path
        
        return config_value
