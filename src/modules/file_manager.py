from pathlib import Path
from typing import List

from .config_manager import ConfigManager


class FileManager:
    def __init__(self, config: ConfigManager):
        self.config = config
        folder = self.config.get('general', 'video_folder_path', 'videos')
        self.video_dir = Path(folder)
        self.supported_formats = self.config.get('general', 'supported_formats', ['.mp4', '.avi', '.mov'])
        self.video_dir.mkdir(exist_ok=True)

    def scan_videos(self) -> List[Path]:
        files: List[Path] = []
        for ext in self.supported_formats:
            files.extend(self.video_dir.glob(f'*{ext}'))
        return files
