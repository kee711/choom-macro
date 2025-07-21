#!/usr/bin/env python3
"""
수동으로 실패한 파일을 smart_extraction_results.json에서 삭제하는 스크립트
"""

import sys
from pathlib import Path

# src 모듈을 import하기 위해 경로 추가
sys.path.append(str(Path(__file__).parent / "src"))

from modules.config_manager import ConfigManager
from modules.smart_file_manager import SmartFileManager
from modules.logger import setup_logger

def list_files_in_folder(smart_manager, folder_name):
    """특정 폴더의 파일들을 나열"""
    if folder_name not in smart_manager.extraction_results:
        print(f"❌ Folder '{folder_name}' not found")
        return []
    
    folder_data = smart_manager.extraction_results[folder_name]
    print(f"\n📁 Files in folder '{folder_name}':")
    print("-" * 50)
    
    for i, item in enumerate(folder_data, 1):
        filename = item.get('original_filename', 'Unknown')
        artist = item.get('artist', 'Unknown')
        title = item.get('title', 'Unknown')
        print(f"{i:2d}. {filename}")
        print(f"    Artist: {artist}, Title: {title}")
    
    return folder_data

def main():
    """메인 함수"""
    config = ConfigManager()
    smart_manager = SmartFileManager(config)
    logger = setup_logger('remove_failed', 'INFO')
    
    print("🗑️ Failed File Removal Tool")
    print("=" * 40)
    
    # 사용 가능한 폴더 목록 표시
    folders = smart_manager.get_available_folders()
    if not folders:
        print("❌ No folders found in extraction results")
        return
    
    print("\n📂 Available folders:")
    for i, folder in enumerate(folders, 1):
        folder_count = len(smart_manager.extraction_results[folder])
        print(f"{i:2d}. {folder} ({folder_count} files)")
    
    # 폴더 선택
    try:
        folder_choice = input(f"\nSelect folder (1-{len(folders)}) or enter folder name: ").strip()
        
        if folder_choice.isdigit():
            folder_idx = int(folder_choice) - 1
            if 0 <= folder_idx < len(folders):
                selected_folder = folders[folder_idx]
            else:
                print("❌ Invalid folder number")
                return
        else:
            if folder_choice in folders:
                selected_folder = folder_choice
            else:
                print(f"❌ Folder '{folder_choice}' not found")
                return
    except KeyboardInterrupt:
        print("\n⛔ Cancelled by user")
        return
    
    # 선택된 폴더의 파일들 나열
    folder_data = list_files_in_folder(smart_manager, selected_folder)
    if not folder_data:
        print("❌ No files found in folder")
        return
    
    # 삭제할 파일 선택
    try:
        file_choice = input(f"\nSelect file to remove (1-{len(folder_data)}) or enter filename: ").strip()
        
        if file_choice.isdigit():
            file_idx = int(file_choice) - 1
            if 0 <= file_idx < len(folder_data):
                selected_filename = folder_data[file_idx].get('original_filename', '')
            else:
                print("❌ Invalid file number")
                return
        else:
            # 파일명으로 검색
            matching_files = [item for item in folder_data 
                            if file_choice.lower() in item.get('original_filename', '').lower()]
            if len(matching_files) == 1:
                selected_filename = matching_files[0].get('original_filename', '')
            elif len(matching_files) > 1:
                print(f"❌ Multiple files match '{file_choice}'. Please be more specific.")
                return
            else:
                print(f"❌ No file found matching '{file_choice}'")
                return
    except KeyboardInterrupt:
        print("\n⛔ Cancelled by user")
        return
    
    # 확인
    print(f"\n⚠️ Are you sure you want to remove this file?")
    print(f"   Folder: {selected_folder}")
    print(f"   File: {selected_filename}")
    
    try:
        confirm = input("Type 'yes' to confirm: ").strip().lower()
        if confirm != 'yes':
            print("❌ Operation cancelled")
            return
    except KeyboardInterrupt:
        print("\n⛔ Cancelled by user")
        return
    
    # 삭제 실행
    if smart_manager.remove_failed_file(selected_folder, selected_filename):
        print(f"✅ Successfully removed '{selected_filename}' from '{selected_folder}'")
        
        # 업데이트된 폴더 상태 표시
        remaining_count = len(smart_manager.extraction_results[selected_folder])
        print(f"📊 Remaining files in folder: {remaining_count}")
    else:
        print(f"❌ Failed to remove '{selected_filename}'")

if __name__ == '__main__':
    main()