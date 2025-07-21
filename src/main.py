from pathlib import Path
from time import sleep
import random

from modules.config_manager import ConfigManager
from modules.smart_file_manager import SmartFileManager
from modules.web_automator import WebAutomator
from modules.account_manager import AccountManager, MultiAccountUploadTracker
from modules.logger import setup_logger


def generate_dynamic_description(artist: str, title: str) -> str:
    """아티스트와 제목을 기반으로 동적 설명 생성"""
    # KPOP 관련 해시태그 풀
    kpop_hashtags = [
        '#kpop', '#dance', '#shorts', '#cover', '#choreo', '#choreography', 
        '#dancing', '#kdance', '#kpopdance', '#dancechallenge', '#viral',
        '#trending', '#fyp', '#music', '#korean', '#idol', '#performance',
        '#moves', '#rhythm', '#beat', '#style', '#cool', '#lit', '#energy'
    ]
    
    # 랜덤으로 3개 해시태그 선택 (중복 없이)
    selected_hashtags = random.sample(kpop_hashtags, 3)
    hashtags_str = ' '.join(selected_hashtags)
    
    # 동적 설명 생성
    description = f"{artist} - {title} dance cover {hashtags_str}"
    return description


def main(account_range=None):
    config = ConfigManager()
    logger = setup_logger('main', config.get('general', 'log_level', 'INFO'))
    smart_file_manager = SmartFileManager(config)
    automator = WebAutomator(config)
    account_manager = AccountManager()
    tracker = MultiAccountUploadTracker()

    delay = config.get('general', 'upload_delay_seconds', 5)
    max_uploads_per_account = 50  # 계정당 최대 업로드 개수

    # 계정 매핑 정보 가져오기 (50개 제한 적용)
    account_mappings = account_manager.get_account_mappings(max_uploads_per_account, account_range)
    
    if not account_mappings:
        logger.info("✅ All accounts have completed uploads or no valid accounts found")
        return
    
    logger.info(f"🚀 Starting multi-account upload process for {len(account_mappings)} accounts")
    logger.info("📊 Upload completion check based on high confidence files in smart_extraction_results.json")
    logger.info("🎯 Only processing files with confidence='high' from smart_extraction_results.json")
    logger.info(f"🔢 Maximum uploads per account: {max_uploads_per_account}")

    try:
        # 각 계정별로 순차 처리
        for mapping in account_mappings:
            email = mapping['email']
            password = mapping['password']
            folder = mapping['folder']
            
            if not folder:
                logger.warning(f"⚠️ Skipping {email}: No folder assigned")
                continue
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 Processing account: {email}")
            logger.info(f"📁 Assigned folder: {folder}")
            logger.info(f"{'='*60}")
            
            # 1. 로그인
            try:
                automator.login_with_account(email, password)
            except Exception as e:
                logger.error(f"❌ Login failed for {email}: {str(e)}")
                # 로그인 실패 시에도 즉시 재시작 트리거
                logger.error(f'🔄 Login failed - triggering restart to retry with fresh browser session')
                automator.close()
                return False
            
            # 2. 해당 폴더의 비디오 파일들 가져오기 (high confidence만)
            folder_videos = smart_file_manager.get_folder_videos(folder)
            logger.info(f"📄 Found {len(folder_videos)} high confidence videos in folder '{folder}'")
            
            if not folder_videos:
                logger.warning(f"⚠️ No videos found for {email} in folder '{folder}'")
                # 로그아웃 후 다음 계정으로
                automator.logout()
                continue
            
            uploaded_count = 0
            current_account_uploads = mapping.get('uploaded_count', 0)
            
            # 3. 폴더 내 비디오들 업로드 (계정당 최대 50개 제한)
            for video_path, artist, title, final_format in folder_videos:
                # 현재 계정의 총 업로드 수가 50개에 도달했는지 확인
                if current_account_uploads >= max_uploads_per_account:
                    logger.info(f"🔢 Account {email} reached maximum uploads ({max_uploads_per_account}), moving to next account")
                    break
                # 중복 업로드 체크 (계정별)
                if tracker.is_uploaded(email, video_path.name):
                    logger.info(f'⏭️ Skipping already uploaded file for {email}: {video_path.name}')
                    continue
                
                # title이 없으면 건너뛰기
                if not title:
                    logger.warning(f'⚠️ Skipping file with no title: {video_path.name}')
                    continue
                    
                logger.info(f'📤 Processing {video_path.name}')
                logger.info(f'🎵 Smart extracted - Artist: {artist}, Title: {title}')
                
                # 동적 설명 생성
                display_artist = artist if artist and artist.lower() != 'null' else title
                description = generate_dynamic_description(display_artist, title)
                logger.info(f'📝 Generated description: {description}')
                
                # 업로드 실행
                if artist and artist.lower() != 'null':
                    upload_artist = artist
                    upload_title = title
                else:
                    upload_artist = ""
                    upload_title = title
                
                # MultiAccountUploadTracker를 사용하여 업로드
                class AccountSpecificTracker:
                    def __init__(self, tracker, email):
                        self.tracker = tracker
                        self.email = email
                    
                    def mark_as_uploaded(self, filename, artist="", title=""):
                        self.tracker.mark_as_uploaded(self.email, filename, artist, title)
                
                account_tracker = AccountSpecificTracker(tracker, email)
                try:
                    success = automator.upload_video(video_path, upload_artist, upload_title, description, account_tracker)
                    
                    if success:
                        uploaded_count += 1
                        current_account_uploads += 1
                        # 즉시 accounts.json의 uploaded_count 증가
                        account_manager.increment_uploaded_count(email)
                        logger.info(f'✅ Successfully uploaded {video_path.name} for {email} (total: {current_account_uploads})')
                    else:
                        logger.error(f'❌ Failed to upload {video_path.name} for {email}')
                        
                        # 업로드 실패 시 즉시 프로그램 종료하여 재시작 트리거
                        logger.error(f'🔄 Upload failed - triggering restart to retry with fresh browser session')
                        automator.close()
                        return False
                        
                except Exception as e:
                    logger.error(f'❌ Upload error for {video_path.name}: {str(e)}')
                    
                    # Exception 발생 시에도 즉시 프로그램 종료하여 재시작 트리거
                    logger.error(f'🔄 Upload exception - triggering restart to retry with fresh browser session')
                    automator.close()
                    return False
                    
                sleep(delay)
            
            # 4. 계정별 업로드 카운트 업데이트
            final_count = mapping.get('uploaded_count', 0) + uploaded_count
            account_manager.update_uploaded_count(email, final_count)
            logger.info(f"📊 Account {email} completed: {uploaded_count} new files uploaded (total: {final_count}/{max_uploads_per_account})")
            
            # 5. 로그아웃
            logger.info(f"🚪 Logging out from {email}")
            automator.logout()
            sleep(2)  # 로그아웃 완료 대기
            
            logger.info(f"✅ Account {email} processing completed\n")
        
        logger.info("🎉 All accounts processed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Critical error in main process: {str(e)}")
        return False
    finally:
        logger.info("🔚 Closing browser")
        automator.close()
    
    return True


if __name__ == '__main__':
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-account upload automation')
    parser.add_argument('--account-range', type=str, help='Account ID range (e.g., "1-10")')
    args = parser.parse_args()
    
    success = main(args.account_range)
    if success:
        sys.exit(0)  # 성공
    else:
        sys.exit(1)  # 실패
