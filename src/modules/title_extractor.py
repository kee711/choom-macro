import json
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

from .config_manager import ConfigManager


class TitleExtractor:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.patterns = self._load_patterns()
        self.remove_keywords = self.config.get('title_extraction', 'remove_keywords', [])
        self.artist_mapping = self._load_artist_mapping()

    def _load_patterns(self):
        pattern_file = Path('config/title_patterns.json')
        if pattern_file.exists():
            with pattern_file.open('r', encoding='utf-8') as f:
                return [re.compile(p, re.IGNORECASE) for p in json.load(f)]
        return []

    def _load_artist_mapping(self) -> Dict[str, str]:
        mapping_file = Path('config/artist_mapping.json')
        if mapping_file.exists():
            with mapping_file.open('r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def extract(self, filename: str) -> Optional[Tuple[str, str]]:
        name = Path(filename).stem
        for kw in self.remove_keywords:
            name = re.sub(kw, '', name, flags=re.IGNORECASE)
        name = re.sub(r'[_\-]+', ' ', name).strip()
        for pattern in self.patterns:
            match = pattern.search(name)
            if match:
                artist = match.groupdict().get('artist', '').strip()
                title = match.groupdict().get('title', '').strip()
                if artist in self.artist_mapping:
                    artist = self.artist_mapping[artist]
                return artist, title
        return None
