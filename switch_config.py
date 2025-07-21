#!/usr/bin/env python3
"""
설정 모드 전환 스크립트
"""

import json
import shutil
from pathlib import Path

def switch_config_mode():
    """설정 모드 전환"""
    config_dir = Path("config")
    current_config = config_dir / "config.json"
    balanced_config = config_dir / "config.json"
    speed_config = config_dir / "config_speed.json"
    
    if not config_dir.exists():
        print("❌ Config directory not found")
        return
    
    print("⚙️ Configuration Mode Switcher")
    print("=" * 40)
    print("1. 🚀 SPEED MODE (Maximum speed, less stable)")
    print("   - upload_delay: 1 second")
    print("   - headless: true")
    print("   - implicit_wait: 6 seconds")
    print()
    print("2. ⚖️ BALANCED MODE (Current, good balance)")
    print("   - upload_delay: 2 seconds") 
    print("   - headless: false")
    print("   - implicit_wait: 8 seconds")
    print()
    print("3. 🛡️ STABLE MODE (Maximum stability)")
    print("   - upload_delay: 3 seconds")
    print("   - headless: false") 
    print("   - implicit_wait: 10 seconds")
    print()
    
    try:
        choice = input("Select mode (1/2/3): ").strip()
        
        if choice == "1":
            # Speed mode
            if speed_config.exists():
                shutil.copy(speed_config, current_config)
                print("✅ Switched to SPEED MODE")
                print("⚠️ Warning: This mode is faster but less stable")
            else:
                print("❌ Speed config file not found")
        
        elif choice == "2":
            # Balanced mode (default)
            balanced_settings = {
                "general": {
                    "video_folder_path": "/Users/minsung/Documents/choom-macro/choom/NaYoon",
                    "log_level": "INFO",
                    "max_concurrent_uploads": 1,
                    "upload_description_template": "Uploaded video",
                    "upload_delay_seconds": 2,
                    "supported_formats": [".mp4", ".avi", ".mov"]
                },
                "web_automation": {
                    "browser": "chrome",
                    "headless": False,
                    "implicit_wait": 8,
                    "upload_timeout": 300
                },
                "title_extraction": {
                    "similarity_threshold": 0.8,
                    "remove_keywords": ["Official", "MV", "가사", "lyrics", "커버", "댄스", "cover", "MIRRORED", "dance"],
                    "remove_patterns": [
                        "\\[.*?\\]",
                        "\\(.*?\\)"
                    ]
                }
            }
            
            with current_config.open('w') as f:
                json.dump(balanced_settings, f, indent=2)
            print("✅ Switched to BALANCED MODE")
            
        elif choice == "3":
            # Stable mode
            stable_settings = {
                "general": {
                    "video_folder_path": "/Users/minsung/Documents/choom-macro/choom/NaYoon",
                    "log_level": "INFO",
                    "max_concurrent_uploads": 1,
                    "upload_description_template": "Uploaded video",
                    "upload_delay_seconds": 3,
                    "supported_formats": [".mp4", ".avi", ".mov"]
                },
                "web_automation": {
                    "browser": "chrome",
                    "headless": False,
                    "implicit_wait": 10,
                    "upload_timeout": 360
                },
                "title_extraction": {
                    "similarity_threshold": 0.8,
                    "remove_keywords": ["Official", "MV", "가사", "lyrics", "커버", "댄스", "cover", "MIRRORED", "dance"],
                    "remove_patterns": [
                        "\\[.*?\\]",
                        "\\(.*?\\)"
                    ]
                }
            }
            
            with current_config.open('w') as f:
                json.dump(stable_settings, f, indent=2)
            print("✅ Switched to STABLE MODE")
            
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n⛔ Cancelled by user")

if __name__ == '__main__':
    switch_config_mode()