#!/usr/bin/env python3
"""
파일 다이얼로그 자동 닫기 기능 테스트 스크립트
"""

import sys
from pathlib import Path

# src 모듈을 import하기 위해 경로 추가
sys.path.append(str(Path(__file__).parent / "src"))

from modules.config_manager import ConfigManager
from modules.web_automator import WebAutomator

def test_file_dialog_close():
    """파일 다이얼로그 자동 닫기 기능 테스트"""
    print("🧪 File Dialog Auto-Close Test")
    print("=" * 40)
    
    config = ConfigManager()
    automator = WebAutomator(config)
    
    try:
        print("1. 테스트용 로그인 (테스트 계정 필요)")
        
        # 테스트 계정 정보 (실제 테스트 시 수정 필요)
        test_email = input("Enter test email (or press Enter to skip): ").strip()
        if not test_email:
            print("⏭️ Skipping login test")
            return
        
        test_password = input("Enter test password: ").strip()
        if not test_password:
            print("❌ Password required for test")
            return
        
        print("2. 로그인 중...")
        automator.login_with_account(test_email, test_password)
        print("✅ 로그인 성공")
        
        print("3. 업로드 페이지로 이동...")
        # 업로드 버튼 클릭하여 업로드 페이지로 이동
        automator.open_upload_page()
        print("✅ 업로드 페이지 로드 완료")
        
        print("4. 파일 다이얼로그 자동 닫기 기능 테스트...")
        
        # 임시 테스트 파일 경로 (실제 존재하지 않아도 됨)
        test_file_path = Path("/tmp/test_video.mp4")
        
        print("   - 파일 다이얼로그 닫기 메서드 호출")
        automator._close_file_dialog_if_open()
        print("   ✅ 파일 다이얼로그 닫기 완료")
        
        print("   - 파일 업로드 완료 대기 메서드 테스트")
        automator._wait_for_file_upload_completion(timeout=3)
        print("   ✅ 파일 업로드 완료 대기 테스트 완료")
        
        print("5. 로그아웃...")
        automator.logout()
        print("✅ 로그아웃 완료")
        
        print("\n🎉 모든 테스트 완료!")
        print("\n📋 새로운 기능:")
        print("• 파일 선택 후 자동으로 다이얼로그 닫기")
        print("• ESC 키, JavaScript, 닫기 버튼 등 다양한 방법 시도")
        print("• 파일 업로드 완료 상태 확인")
        print("• 업로드 진행률 모니터링")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        
    finally:
        print("🧹 브라우저 정리 중...")
        automator.close()
        print("✅ 브라우저 정리 완료")

def show_features():
    """추가된 기능들 설명"""
    print("\n🆕 NEW FEATURES ADDED")
    print("=" * 30)
    print("1. 🔒 Auto-close file dialog")
    print("   • 파일 선택 후 다이얼로그 자동 닫기")
    print("   • ESC 키 전송")
    print("   • JavaScript 다이얼로그 닫기")
    print("   • 닫기 버튼 자동 클릭")
    print()
    print("2. ⏳ Upload completion detection")
    print("   • 파일 업로드 완료 상태 감지")
    print("   • 진행률 인디케이터 모니터링")
    print("   • 다음 버튼 활성화 확인")
    print("   • JavaScript 상태 검사")
    print()
    print("3. 🚀 Enhanced user experience")
    print("   • 더 부드러운 업로드 플로우")
    print("   • 자동화된 다이얼로그 관리")
    print("   • 안정적인 파일 선택 프로세스")

if __name__ == '__main__':
    show_features()
    
    run_test = input("\nRun file dialog test? (y/N): ").strip().lower()
    if run_test == 'y':
        test_file_dialog_close()
    else:
        print("📝 Test skipped. Features are ready to use!")