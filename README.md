# Choom Macro

Automates uploading short-form videos to [Hanlim World](https://app.hanlim.world/upload).

## Setup

1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
2. Edit `config/config.json` with your settings and Spotify API credentials.
3. Place videos in the folder specified by `video_folder_path`.

## Usage

```bash
python src/main.py
```

Logs are stored in the `logs/` directory.
