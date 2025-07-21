# Choom Macro

Automates uploading short-form videos to [Hanlim World](https://app.hanlim.world).

## Setup

4k : be1bfa1014b445329c0863038db34dd8

https://docs.google.com/spreadsheets/d/1wkhzuuccI7MlEJAYosNCaUOTTiW-3hCY8yLO1u2ukAw/edit?gid=1359737614#gid=1359737614

1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
2. Edit `config/config.json` with correct video_folder_path
3. Place videos in the folder specified by `video_folder_path`.

## Usage

```bash
python run_with_retry.py 1-10
```

## Title - AI Parser
python smart_title_extractor.py

## Title - Status
python show_confidence_stats.py

Logs are stored in the `logs/` directory.
