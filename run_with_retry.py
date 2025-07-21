#!/usr/bin/env python3
"""
Auto-retry wrapper for main.py
실행 중 실패가 발생하면 자동으로 main.py를 재시작하는 래퍼 스크립트
"""

import subprocess
import sys
import time
import logging
from pathlib import Path

def setup_retry_logger():
    """재시작 로직 전용 로거 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - RETRY - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/retry.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('retry')

def run_main_with_retry(max_retries=15, retry_delay=5, account_range=None):
    """
    main.py를 실행하고 실패 시 자동으로 재시작
    
    Args:
        max_retries (int): 최대 재시작 횟수 (기본값: 5)
        retry_delay (int): 재시작 간격 (초, 기본값: 30)
        account_range (str): 계정 ID 범위 (예: "1-10")
    """
    logger = setup_retry_logger()
    main_script = Path(__file__).parent / "src" / "main.py"
    
    if not main_script.exists():
        logger.error(f"❌ main.py not found at: {main_script}")
        return False
    
    retry_count = 0
    
    logger.info(f"🚀 Starting auto-retry wrapper for main.py")
    logger.info(f"📊 Max retries: {max_retries}, Retry delay: {retry_delay}s")
    
    while retry_count <= max_retries:
        try:
            if retry_count > 0:
                logger.info(f"🔄 Retry attempt {retry_count}/{max_retries}")
                logger.info(f"⏳ Waiting {retry_delay} seconds before restart...")
                time.sleep(retry_delay)
            
            logger.info(f"▶️ Starting main.py (attempt {retry_count + 1})")
            
            # main.py 실행 명령어 구성
            cmd = [sys.executable, str(main_script)]
            if account_range:
                cmd.extend(['--account-range', account_range])
                logger.info(f"🎯 Running with account range: {account_range}")
            
            result = subprocess.run(
                cmd,
                cwd=str(main_script.parent.parent),  # choom-macro 루트 디렉토리에서 실행
                capture_output=False,  # 실시간 로그 출력을 위해 False
                text=True
            )
            
            # 성공적으로 완료된 경우
            if result.returncode == 0:
                logger.info("✅ main.py completed successfully!")
                return True
            else:
                logger.error(f"❌ main.py failed with exit code: {result.returncode}")
                
        except subprocess.TimeoutExpired:
            logger.error("❌ main.py execution timed out")
        except KeyboardInterrupt:
            logger.info("⛔ User interrupted execution")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error running main.py: {str(e)}")
        
        retry_count += 1
        
        if retry_count <= max_retries:
            logger.warning(f"🔄 main.py failed, preparing retry {retry_count}/{max_retries}")
        else:
            logger.error(f"❌ Maximum retries ({max_retries}) exceeded. Giving up.")
            return False
    
    return False

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-retry wrapper for main.py')
    parser.add_argument('--max-retries', type=int, default=15,
                        help='Maximum number of retries (default: 15)')
    parser.add_argument('--retry-delay', type=int, default=5,
                        help='Delay between retries in seconds (default: 5)')
    parser.add_argument('range', nargs='?', help='Account ID range (e.g., "1-10")')
    
    args = parser.parse_args()
    
    # logs 디렉토리 생성
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    success = run_main_with_retry(
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
        account_range=getattr(args, 'range', None)
    )
    
    if success:
        print("\n🎉 Process completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Process failed after all retries")
        sys.exit(1)

if __name__ == '__main__':
    main()