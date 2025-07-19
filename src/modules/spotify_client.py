from typing import Optional, Tuple

from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

from .config_manager import ConfigManager


class SpotifyClient:
    def __init__(self, config: ConfigManager):
        client_id = config.get('spotify', 'client_id')
        client_secret = config.get('spotify', 'client_secret')
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        self.sp = Spotify(auth_manager=auth_manager)
        self.similarity_threshold = config.get('title_extraction', 'similarity_threshold', 0.8)

    def search_track(self, artist: str, title: str) -> Optional[str]:
        query = f"artist:{artist} track:{title}"
        results = self.sp.search(q=query, type='track', limit=1)
        items = results.get('tracks', {}).get('items')
        if items:
            return items[0]['id']
        return None
