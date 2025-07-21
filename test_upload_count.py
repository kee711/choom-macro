#!/usr/bin/env python3
"""
uploaded_count 증가 테스트 스크립트
"""

import sys
from pathlib import Path

# src 모듈을 import하기 위해 경로 추가
sys.path.append(str(Path(__file__).parent / "src"))

from modules.account_manager import AccountManager

def test_increment_count():
    """uploaded_count 증가 테스트"""
    account_manager = AccountManager()
    
    print("📊 Current account status:")
    print("-" * 50)
    
    # 현재 상태 출력
    mappings = account_manager.accounts_data.get('mappings', [])
    for mapping in mappings:
        email = mapping.get('email', 'Unknown')
        folder = mapping.get('folder', 'No folder')
        count = mapping.get('uploaded_count', 0)
        print(f"📧 {email}")
        print(f"   📁 Folder: {folder}")
        print(f"   📈 Uploaded: {count}")
        print()
    
    # 테스트할 이메일 선택
    test_email = input("Enter email to test increment (or press Enter to skip): ").strip()
    
    if test_email:
        if any(m.get('email') == test_email for m in mappings):
            print(f"\n🧪 Testing increment for: {test_email}")
            
            # 현재 카운트 확인
            account_info = account_manager.get_account_info(test_email)
            old_count = account_info.get('uploaded_count', 0) if account_info else 0
            print(f"   Current count: {old_count}")
            
            # 카운트 증가
            new_count = account_manager.increment_uploaded_count(test_email)
            print(f"   New count: {new_count}")
            
            if new_count == old_count + 1:
                print("✅ Increment test PASSED")
            else:
                print("❌ Increment test FAILED")
        else:
            print(f"❌ Email '{test_email}' not found")
    
    print("\n✅ Test completed")

if __name__ == '__main__':
    test_increment_count()