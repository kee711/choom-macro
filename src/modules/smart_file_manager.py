import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config_manager import ConfigManager
from .logger import setup_logger


class SmartFileManager:
    """smart_extraction_results.json을 기반으로 파일을 관리하는 클래스"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = setup_logger(self.__class__.__name__, config.get('general', 'log_level', 'INFO'))
        self.extraction_results = self._load_extraction_results()
        
    def _load_extraction_results(self) -> Dict:
        """smart_extraction_results.json 파일 로드"""
        results_file = Path("smart_extraction_results.json")
        
        if not results_file.exists():
            self.logger.error(f"smart_extraction_results.json 파일을 찾을 수 없습니다: {results_file}")
            return {}
        
        try:
            with results_file.open('r', encoding='utf-8') as f:
                results = json.load(f)
                self.logger.info(f"Loaded smart extraction results for {len(results)} folders")
                return results
        except Exception as e:
            self.logger.error(f"Failed to load extraction results: {str(e)}")
            return {}
    
    def get_folder_videos(self, folder_name: str) -> List[Tuple[Path, str, str, str]]:
        """
        특정 폴더의 비디오 파일들과 메타데이터를 반환
        Returns: List of (file_path, artist, title, final_format)
        """
        if folder_name not in self.extraction_results:
            self.logger.warning(f"Folder '{folder_name}' not found in extraction results")
            return []
        
        folder_data = self.extraction_results[folder_name]
        # choom 폴더 기준으로 경로 구성
        base_path = Path("/Users/minsung/Documents/choom-macro/choom") / folder_name
        
        if not base_path.exists():
            self.logger.error(f"Folder path does not exist: {base_path}")
            return []
        
        results = []
        
        for item in folder_data:
            filename = item.get('original_filename', '')
            artist = item.get('artist')
            title = item.get('title')
            confidence = item.get('confidence', '')
            final_format = item.get('final_format', '')
            
            # confidence가 'high'가 아니면 건너뛰기
            if confidence != 'high':
                self.logger.info(f"⏭️ Skipping file with {confidence} confidence: {filename}")
                continue
            
            # title이 null이면 건너뛰기
            if not title:
                self.logger.warning(f"Skipping file with no title: {filename}")
                continue
            
            # 파일 경로 확인
            file_path = base_path / filename
            if not file_path.exists():
                self.logger.warning(f"File does not exist: {file_path}")
                continue
            
            results.append((file_path, artist, title, final_format))
        
        self.logger.info(f"Found {len(results)} valid videos in folder '{folder_name}'")
        return results
    
    def scan_videos(self) -> List[Tuple[Path, str, str, str]]:
        """
        모든 폴더의 비디오 파일들을 스캔
        Returns: List of (file_path, artist, title, final_format)
        """
        all_videos = []
        
        # 설정된 폴더 경로에서 폴더명 추출
        video_folder_path = self.config.get('general', 'video_folder_path', 'videos')
        current_folder = Path(video_folder_path).name
        
        # 현재 설정된 폴더의 비디오들만 가져오기
        folder_videos = self.get_folder_videos(current_folder)
        all_videos.extend(folder_videos)
        
        self.logger.info(f"Total videos found: {len(all_videos)}")
        return all_videos
    
    def get_search_query(self, artist: Optional[str], title: str) -> str:
        """검색 쿼리 생성"""
        if artist and artist.lower() != 'null':
            return f"{artist} {title}"
        else:
            return title
    
    def get_available_folders(self) -> List[str]:
        """사용 가능한 폴더 목록 반환"""
        return list(self.extraction_results.keys())
    
    def remove_failed_file(self, folder_name: str, filename: str) -> bool:
        """
        실패한 파일을 smart_extraction_results.json에서 삭제
        
        Args:
            folder_name (str): 폴더명
            filename (str): 삭제할 파일명
            
        Returns:
            bool: 삭제 성공 여부
        """
        if folder_name not in self.extraction_results:
            self.logger.warning(f"Folder '{folder_name}' not found in extraction results")
            return False
        
        folder_data = self.extraction_results[folder_name]
        original_count = len(folder_data)
        
        # 해당 파일을 찾아서 삭제
        updated_folder_data = [
            item for item in folder_data 
            if item.get('original_filename', '') != filename
        ]
        
        if len(updated_folder_data) == original_count:
            self.logger.warning(f"File '{filename}' not found in folder '{folder_name}'")
            return False
        
        # 업데이트된 데이터 저장
        self.extraction_results[folder_name] = updated_folder_data
        
        # 파일에 저장
        if self._save_extraction_results():
            self.logger.info(f"✅ Removed failed file '{filename}' from folder '{folder_name}'")
            return True
        else:
            self.logger.error(f"❌ Failed to save extraction results after removing '{filename}'")
            return False
    
    def _save_extraction_results(self) -> bool:
        """extraction_results를 파일에 저장"""
        results_file = Path("smart_extraction_results.json")
        
        try:
            with results_file.open('w', encoding='utf-8') as f:
                json.dump(self.extraction_results, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save extraction results: {str(e)}")
            return False