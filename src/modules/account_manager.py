import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .logger import setup_logger


class AccountManager:
    """계정별 업로드 관리 클래스"""
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__, 'INFO')
        self.accounts_file = Path("accounts.json")
        self.accounts_data = self._load_accounts()
        
    def _load_accounts(self) -> Dict:
        """accounts.json 파일 로드"""
        if not self.accounts_file.exists():
            self.logger.error("accounts.json 파일을 찾을 수 없습니다.")
            return {}
        
        try:
            with self.accounts_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
                self.logger.info(f"Loaded {len(data.get('mappings', []))} account mappings")
                return data
        except Exception as e:
            self.logger.error(f"Failed to load accounts.json: {str(e)}")
            return {}
    
    def get_account_mappings(self, max_uploads_per_account=50, account_range=None) -> List[Dict]:
        """폴더가 매핑되고 업로드가 완료되지 않은 계정 목록만 반환"""
        mappings = self.accounts_data.get('mappings', [])
        
        # account_range가 지정된 경우 범위 파싱 및 필터링
        if account_range:
            start_id, end_id = self._parse_account_range(account_range)
            mappings = [m for m in mappings if start_id <= m.get('id', 0) <= end_id]
            self.logger.info(f"Filtering accounts by range {account_range}: {len(mappings)} accounts found")
        
        valid_mappings = []
        
        # smart_extraction_results.json 로드
        extraction_results = self._load_smart_extraction_results()
        
        for mapping in mappings:
            folder = mapping.get('folder')
            uploaded_count = mapping.get('uploaded_count', 0)
            
            # 폴더가 매핑되지 않은 경우 제외
            if not folder:
                self.logger.info(f"Skipping {mapping.get('email')}: No folder assigned")
                continue
            
            # 계정당 최대 업로드 개수 체크 (50개 제한)
            if uploaded_count >= max_uploads_per_account:
                self.logger.info(f"Skipping {mapping.get('email')}: Reached maximum uploads ({uploaded_count}/{max_uploads_per_account})")
                continue
            
            # smart_extraction_results에서 해당 폴더의 high confidence 파일 개수 확인
            high_confidence_count = self._get_high_confidence_count(extraction_results, folder)
            
            # 업로드된 개수가 high confidence 개수보다 같거나 많으면 제외
            if uploaded_count >= high_confidence_count:
                self.logger.info(f"Skipping {mapping.get('email')}: All files uploaded ({uploaded_count}/{high_confidence_count} high confidence files)")
                continue
            
            # 남은 업로드 가능 개수 계산
            remaining_uploads = min(max_uploads_per_account - uploaded_count, high_confidence_count - uploaded_count)
            
            valid_mappings.append(mapping)
            self.logger.info(f"Including {mapping.get('email')}: {uploaded_count}/{min(max_uploads_per_account, high_confidence_count)} files uploaded, {remaining_uploads} remaining")
        
        self.logger.info(f"Found {len(valid_mappings)} accounts ready for upload (max {max_uploads_per_account} per account)")
        return valid_mappings
    
    def _parse_account_range(self, range_str: str) -> Tuple[int, int]:
        """계정 범위 문자열을 파싱하여 시작 ID와 끝 ID 반환"""
        try:
            if '-' in range_str:
                start, end = range_str.split('-')
                start_id = int(start.strip())
                end_id = int(end.strip())
            else:
                # 단일 ID인 경우
                start_id = end_id = int(range_str.strip())
            
            self.logger.info(f"Parsed account range: {start_id} to {end_id}")
            return start_id, end_id
        except ValueError as e:
            self.logger.error(f"Invalid account range format '{range_str}': {str(e)}")
            return 1, 30  # 기본값으로 전체 범위 반환
    
    def _load_smart_extraction_results(self) -> Dict:
        """smart_extraction_results.json 로드"""
        results_file = Path("smart_extraction_results.json")
        
        if not results_file.exists():
            self.logger.warning("smart_extraction_results.json not found")
            return {}
        
        try:
            with results_file.open('r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load smart_extraction_results.json: {str(e)}")
            return {}
    
    def _get_high_confidence_count(self, extraction_results: Dict, folder_name: str) -> int:
        """특정 폴더의 high confidence 파일 개수 반환"""
        if folder_name not in extraction_results:
            self.logger.warning(f"Folder '{folder_name}' not found in extraction results")
            return 0
        
        folder_data = extraction_results[folder_name]
        high_confidence_count = sum(1 for item in folder_data if item.get('confidence') == 'high')
        
        self.logger.debug(f"Folder '{folder_name}': {high_confidence_count} high confidence files")
        return high_confidence_count
    
    def update_uploaded_count(self, email: str, count: int):
        """특정 계정의 업로드 카운트 업데이트"""
        mappings = self.accounts_data.get('mappings', [])
        
        for mapping in mappings:
            if mapping.get('email') == email:
                mapping['uploaded_count'] = count
                break
        
        # 파일 저장
        try:
            with self.accounts_file.open('w', encoding='utf-8') as f:
                json.dump(self.accounts_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Updated upload count for {email}: {count}")
        except Exception as e:
            self.logger.error(f"Failed to update accounts.json: {str(e)}")
    
    def increment_uploaded_count(self, email: str):
        """특정 계정의 업로드 카운트를 1 증가"""
        mappings = self.accounts_data.get('mappings', [])
        
        for mapping in mappings:
            if mapping.get('email') == email:
                current_count = mapping.get('uploaded_count', 0)
                new_count = current_count + 1
                mapping['uploaded_count'] = new_count
                
                # 즉시 파일 저장
                try:
                    with self.accounts_file.open('w', encoding='utf-8') as f:
                        json.dump(self.accounts_data, f, ensure_ascii=False, indent=2)
                    self.logger.info(f"✅ Incremented upload count for {email}: {current_count} → {new_count}")
                    return new_count
                except Exception as e:
                    self.logger.error(f"Failed to save incremented count for {email}: {str(e)}")
                    return current_count
        
        self.logger.warning(f"Account {email} not found for count increment")
        return 0
    
    def get_account_info(self, email: str) -> Optional[Dict]:
        """특정 이메일의 계정 정보 반환"""
        mappings = self.accounts_data.get('mappings', [])
        
        for mapping in mappings:
            if mapping.get('email') == email:
                return mapping
        
        return None


class MultiAccountUploadTracker:
    """계정별 업로드 추적 클래스"""
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__, 'INFO')
        self.tracker_file = Path("logs/uploaded_files.json")
        self.uploaded_data = self._load_uploaded_data()
        
    def _load_uploaded_data(self) -> Dict:
        """uploaded_files.json 로드"""
        if not self.tracker_file.exists():
            self.logger.info("No uploaded files tracker found, starting fresh")
            return {}
        
        try:
            with self.tracker_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
                total_files = sum(len(files) for files in data.values())
                self.logger.info(f"Loaded upload tracker with {total_files} files across {len(data)} accounts")
                return data
        except Exception as e:
            self.logger.error(f"Failed to load upload tracker: {str(e)}")
            return {}
    
    def _save_uploaded_data(self):
        """uploaded_files.json 저장"""
        try:
            self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
            with self.tracker_file.open('w', encoding='utf-8') as f:
                json.dump(self.uploaded_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save upload tracker: {str(e)}")
    
    def is_uploaded(self, email: str, filename: str) -> bool:
        """특정 계정에서 파일이 업로드되었는지 확인"""
        account_files = self.uploaded_data.get(email, {})
        return filename in account_files
    
    def mark_as_uploaded(self, email: str, filename: str, artist: str = "", title: str = ""):
        """특정 계정에서 파일을 업로드 완료로 표시"""
        if email not in self.uploaded_data:
            self.uploaded_data[email] = {}
        
        from datetime import datetime
        upload_info = {
            "upload_date": datetime.now().isoformat(),
            "artist": artist,
            "title": title
        }
        
        self.uploaded_data[email][filename] = upload_info
        self._save_uploaded_data()
        self.logger.info(f"Marked as uploaded for {email}: {filename}")
    
    def get_uploaded_count(self, email: str) -> int:
        """특정 계정의 업로드된 파일 개수 반환"""
        return len(self.uploaded_data.get(email, {}))
    
    def get_uploaded_files(self, email: str) -> Dict:
        """특정 계정의 업로드된 파일 목록 반환"""
        return self.uploaded_data.get(email, {})