import json
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, Any

from .logger import setup_logger


class UploadTracker:
    """업로드된 파일들을 추적하여 중복 업로드를 방지하는 클래스"""
    
    def __init__(self, tracker_file: str = "logs/uploaded_files.json"):
        self.tracker_file = Path(tracker_file)
        self.logger = setup_logger(self.__class__.__name__, 'INFO')
        self.uploaded_files = self._load_uploaded_files()
        
    def _load_uploaded_files(self) -> Dict[str, Any]:
        """업로드된 파일 목록을 JSON에서 로드"""
        if self.tracker_file.exists():
            try:
                with self.tracker_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.info(f'Loaded {len(data)} uploaded files from tracker')
                    return data
            except Exception as e:
                self.logger.error(f'Failed to load tracker file: {str(e)}')
                return {}
        else:
            self.logger.info('No tracker file found, starting fresh')
            return {}
    
    def _save_uploaded_files(self):
        """업로드된 파일 목록을 JSON에 저장"""
        try:
            # logs 디렉토리가 없으면 생성
            self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
            
            with self.tracker_file.open('w', encoding='utf-8') as f:
                json.dump(self.uploaded_files, f, ensure_ascii=False, indent=2)
            self.logger.info(f'Saved tracker file with {len(self.uploaded_files)} entries')
        except Exception as e:
            self.logger.error(f'Failed to save tracker file: {str(e)}')
    
    def is_uploaded(self, filename: str) -> bool:
        """파일이 이미 업로드되었는지 확인"""
        return filename in self.uploaded_files
    
    def mark_as_uploaded(self, filename: str, artist: str = "", title: str = ""):
        """파일을 업로드 완료로 표시"""
        upload_info = {
            "upload_date": datetime.now().isoformat(),
            "artist": artist,
            "title": title
        }
        self.uploaded_files[filename] = upload_info
        self._save_uploaded_files()
        self.logger.info(f'Marked as uploaded: {filename}')
    
    def get_uploaded_count(self) -> int:
        """업로드된 파일 개수 반환"""
        return len(self.uploaded_files)
    
    def get_uploaded_files(self) -> Set[str]:
        """업로드된 파일명 목록 반환"""
        return set(self.uploaded_files.keys())
    
    def remove_from_tracker(self, filename: str):
        """트래커에서 파일 제거 (재업로드 필요 시 사용)"""
        if filename in self.uploaded_files:
            del self.uploaded_files[filename]
            self._save_uploaded_files()
            self.logger.info(f'Removed from tracker: {filename}')
    
    def clear_all(self):
        """모든 트래킹 데이터 삭제"""
        self.uploaded_files.clear()
        self._save_uploaded_files()
        self.logger.info('Cleared all tracking data')