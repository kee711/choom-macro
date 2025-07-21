import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)


def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    level = getattr(logging, level.upper(), logging.INFO)
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        file_handler = RotatingFileHandler(
            LOG_DIR / 'app.log', maxBytes=1_000_000, backupCount=3)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
