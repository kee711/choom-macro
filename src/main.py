from pathlib import Path
from time import sleep

from modules.config_manager import ConfigManager
from modules.file_manager import FileManager
from modules.title_extractor import TitleExtractor
from modules.spotify_client import SpotifyClient
from modules.web_automator import WebAutomator
from modules.logger import setup_logger


def main():
    config = ConfigManager()
    logger = setup_logger('main', config.get('general', 'log_level', 'INFO'))
    file_manager = FileManager(config)
    extractor = TitleExtractor(config)
    spotify = SpotifyClient(config)
    automator = WebAutomator(config)

    description_template = config.get('general', 'upload_description_template', 'Uploaded video')
    delay = config.get('general', 'upload_delay_seconds', 5)

    try:
        automator.open_upload_page()
        for video in file_manager.scan_videos():
            logger.info(f'Processing {video.name}')
            result = extractor.extract(video.name)
            if not result:
                logger.warning(f'Could not extract title from {video.name}')
                continue
            artist, title = result
            track_id = spotify.search_track(artist, title)
            if not track_id:
                logger.warning(f'Spotify search failed for {artist} - {title}')
            description = description_template
            automator.upload_video(video, description)
            logger.info(f'Uploaded {video.name}')
            sleep(delay)
    finally:
        automator.close()


if __name__ == '__main__':
    main()
