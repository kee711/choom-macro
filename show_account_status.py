#!/usr/bin/env python3
"""
계정별 업로드 상태를 보여주는 스크립트 (50개 제한 포함)
"""

import sys
from pathlib import Path

# src 모듈을 import하기 위해 경로 추가
sys.path.append(str(Path(__file__).parent / "src"))

from modules.account_manager import AccountManager

def show_account_status():
    """계정별 업로드 상태 표시"""
    account_manager = AccountManager()
    max_uploads = 50
    
    print("👥 Account Upload Status")
    print("=" * 60)
    print(f"📋 Maximum uploads per account: {max_uploads}")
    print()
    
    mappings = account_manager.accounts_data.get('mappings', [])
    
    if not mappings:
        print("❌ No account mappings found")
        return
    
    # 상태별 분류
    completed_accounts = []
    active_accounts = []
    no_folder_accounts = []
    
    for mapping in mappings:
        email = mapping.get('email', 'Unknown')
        folder = mapping.get('folder')
        uploaded_count = mapping.get('uploaded_count', 0)
        
        if not folder:
            no_folder_accounts.append((email, uploaded_count))
        elif uploaded_count >= max_uploads:
            completed_accounts.append((email, folder, uploaded_count))
        else:
            active_accounts.append((email, folder, uploaded_count))
    
    # 활성 계정 (아직 50개 미만)
    if active_accounts:
        print("🟢 ACTIVE ACCOUNTS (Less than 50 uploads)")
        print("-" * 50)
        for email, folder, count in active_accounts:
            remaining = max_uploads - count
            progress = (count / max_uploads) * 100
            print(f"📧 {email}")
            print(f"   📁 Folder: {folder}")
            print(f"   📊 Progress: {count}/{max_uploads} ({progress:.1f}%)")
            print(f"   🆕 Remaining: {remaining} uploads")
            print()
    
    # 완료된 계정 (50개 달성)
    if completed_accounts:
        print("✅ COMPLETED ACCOUNTS (50 uploads reached)")
        print("-" * 50)
        for email, folder, count in completed_accounts:
            print(f"📧 {email}")
            print(f"   📁 Folder: {folder}")
            print(f"   ✨ Uploads: {count}/{max_uploads} (100%)")
            print()
    
    # 폴더 미할당 계정
    if no_folder_accounts:
        print("⚪ NO FOLDER ASSIGNED")
        print("-" * 50)
        for email, count in no_folder_accounts:
            print(f"📧 {email}")
            print(f"   📁 Folder: Not assigned")
            print(f"   📊 Uploads: {count}")
            print()
    
    # 전체 통계
    print("📊 OVERALL STATISTICS")
    print("-" * 30)
    print(f"   🟢 Active accounts: {len(active_accounts)}")
    print(f"   ✅ Completed accounts: {len(completed_accounts)}")
    print(f"   ⚪ No folder accounts: {len(no_folder_accounts)}")
    print(f"   📱 Total accounts: {len(mappings)}")
    
    if active_accounts:
        total_active_uploads = sum(count for _, _, count in active_accounts)
        total_remaining = len(active_accounts) * max_uploads - total_active_uploads
        print(f"   📈 Total active uploads: {total_active_uploads}")
        print(f"   🆕 Total remaining slots: {total_remaining}")
    
    if completed_accounts:
        total_completed_uploads = sum(count for _, _, count in completed_accounts)
        print(f"   🎯 Total completed uploads: {total_completed_uploads}")

if __name__ == '__main__':
    show_account_status()