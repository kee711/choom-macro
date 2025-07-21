import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import openai
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

class SmartTitleExtractor:
    def __init__(self, openai_api_key: str):
        """OpenAI API를 사용하는 스마트 제목 추출기"""
        self.client = openai.OpenAI(api_key=openai_api_key)
        
    def clean_filename(self, filename: str) -> str:
        """파일명 기본 정리"""
        name = Path(filename).stem
        
        # 패턴 제거 (괄호, 대괄호 등)
        remove_patterns = [
            r'\[.*?\]',    # [MIRRORED], [MV] 등
            r'\([^)]*\)',  # 모든 괄호 내용
        ]
        
        for pattern in remove_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # 키워드 제거
        remove_keywords = [
            "dance", "cover", "MIRRORED", "feat", "featuring", 
            "official", "mv", "music video", "choreography", "choreo"
        ]
        
        for kw in remove_keywords:
            name = re.sub(r'\b' + re.escape(kw) + r'\b', '', name, flags=re.IGNORECASE)
        
        # 연속된 공백, 언더스코어, 하이픈을 하나의 공백으로 변환
        name = re.sub(r'[_\-\s]+', ' ', name).strip()
        
        return name
    
    def extract_with_openai(self, filenames: List[str]) -> List[Dict]:
        """OpenAI API를 사용하여 배치로 아티스트와 제목 추출"""
        
        # 파일명 정리
        cleaned_names = [self.clean_filename(f) for f in filenames]
        
        # OpenAI 프롬프트 생성
        prompt = f"""다음은 K-pop 댄스 커버 영상의 파일명들입니다. 각 파일명에서 아티스트명과 노래 제목을 추출해주세요.

규칙:
1. 아티스트 이름과 노래 제목이 파일명, 해시태그에 명확하게 들어가 있지 않으면 null로 설정
2. 아티스트 이름, 노래 이름은 파일명, 해시태그에 정확히 포함되어있어야 함. 파일명에 들어있지 않은 아티스트 이름, 노래 이름을 멋대로 추론해내지 말 것
3. 각 결과는 JSON 형식으로 반환
4. 파일명에 명확하게 들어가 있지 않으면 null로 설정

추출 예시 :
    "folder": "EXRAL PRODUCTION",
    "original_filename": "🇮🇩 Kpop In Public GIDLE - DUMDi DUMBDi  #XRPD #RandomPlayDance #Shorts.mp4",
    "cleaned_filename": "🇮🇩 Kpop In Public GIDLE DUMDi DUMBDi #XRPD #RandomPlayDance #Shorts",
    "artist": "GIDLE",
    "title": "DUMDi DUMBDi",
    "confidence": "high",
    "final_format": "GIDLE - DUMDi DUMBDi"

주의사항: 
- 파일명에 들어있지 않은 아티스트 이름, 노래 이름을 멋대로 추론해내지 말 것
- 오로지 파일명에 들어있는 아티스트 이름, 노래 이름만 추출해내야 함

파일명 목록:
{chr(10).join([f"{i+1}. 원본: {orig}, 정리됨: {clean}" for i, (orig, clean) in enumerate(zip(filenames, cleaned_names))])}

각 파일명에 대해 다음 JSON 형식으로 응답해주세요:
{{
  "original_filename": "원본 파일명 그대로",
  "cleaned_filename": "정리된 파일명",
  "artist": "아티스트명 또는 null",
  "title": "노래 제목",
  "confidence": "high/medium/low",
  "final_format": "아티스트 - 제목 형태"
}}

전체 응답은 JSON 배열 형태로 해주세요."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 K-pop 전문가입니다. 파일명에서 아티스트와 노래 제목을 정확하게 추출하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # JSON 응답 파싱
            content = response.choices[0].message.content
            
            # JSON 블록 추출 (```json ... ``` 형태인 경우)
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            results = json.loads(content)
            
            # OpenAI가 완전한 형태로 응답했으므로 그대로 사용
            final_results = []
            for result in results:
                # folder 정보만 추가
                result["folder"] = ""  # 나중에 설정
                final_results.append(result)
            
            return final_results
            
        except Exception as e:
            print(f"OpenAI API 오류: {str(e)}")
            # 오류 시 기본 처리
            results = []
            for i, filename in enumerate(filenames):
                results.append({
                    "folder": "",
                    "original_filename": filename,
                    "cleaned_filename": cleaned_names[i],
                    "artist": None,
                    "title": cleaned_names[i],
                    "confidence": "low",
                    "final_format": cleaned_names[i],
                    "error": str(e)
                })
            return results

    def _load_existing_results(self) -> Dict[str, List[Dict]]:
        """기존 smart_extraction_results.json 로드"""
        results_file = Path("smart_extraction_results.json")
        
        if not results_file.exists():
            print("📄 기존 결과 파일이 없습니다. 새로 시작합니다.")
            return {}
        
        try:
            with results_file.open('r', encoding='utf-8') as f:
                existing_results = json.load(f)
                print(f"📋 기존 결과 로드: {len(existing_results)}개 폴더")
                return existing_results
        except Exception as e:
            print(f"⚠️ 기존 결과 파일 로드 실패: {str(e)}")
            return {}

    def process_choom_folders(self, choom_base_path: str) -> Dict[str, List[Dict]]:
        """choom 폴더 내 모든 하위 폴더를 순회하며 파일명 처리"""
        
        choom_path = Path(choom_base_path)
        if not choom_path.exists():
            raise FileNotFoundError(f"choom 폴더를 찾을 수 없습니다: {choom_base_path}")
        
        # 기존 결과 로드
        all_results = self._load_existing_results()
        
        # 모든 하위 폴더 찾기
        for folder_path in choom_path.iterdir():
            if folder_path.is_dir():
                folder_name = folder_path.name
                
                # 비디오 파일 찾기
                video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
                video_files = []
                
                for ext in video_extensions:
                    video_files.extend(folder_path.glob(f"*{ext}"))
                    video_files.extend(folder_path.glob(f"*{ext.upper()}"))
                
                if not video_files:
                    print(f"  📂 {folder_name}에서 비디오 파일을 찾지 못했습니다.")
                    continue
                
                current_video_files = [f.name for f in video_files]
                
                # 이미 처리된 폴더인지 확인하고 누락된 파일이 있는지 체크
                if folder_name in all_results:
                    existing_files = [item['original_filename'] for item in all_results[folder_name]]
                    missing_files = [f for f in current_video_files if f not in existing_files]
                    
                    if not missing_files:
                        print(f"⏭️ 건너뜀: {folder_name} 폴더 (모든 {len(current_video_files)}개 파일 이미 처리됨)")
                        continue
                    else:
                        print(f"🔄 증분 처리: {folder_name} 폴더 ({len(missing_files)}개 새 파일 발견)")
                        filenames_to_process = missing_files
                        is_incremental = True
                else:
                    print(f"\n🔄 처리 중: {folder_name} 폴더")
                    filenames_to_process = current_video_files
                    is_incremental = False
                
                print(f"  📄 {len(filenames_to_process)}개의 비디오 파일 {'증분 ' if is_incremental else ''}처리 예정")
                
                # OpenAI로 배치 처리
                print(f"  🤖 OpenAI API로 분석 중...")
                results = self.extract_with_openai(filenames_to_process)
                
                # 폴더명 추가
                for result in results:
                    result["folder"] = folder_name
                
                # 증분 업데이트인 경우 기존 결과에 추가, 아니면 새로 설정
                if is_incremental:
                    all_results[folder_name].extend(results)
                    print(f"  ✅ {folder_name} 폴더 증분 처리 완료 (+{len(results)}개)")
                else:
                    all_results[folder_name] = results
                    print(f"  ✅ {folder_name} 폴더 처리 완료 ({len(results)}개)")
                
                # 중간 저장 (API 오류 시 복구를 위해)
                self._save_intermediate_results(all_results)
        
        return all_results
    
    def _save_intermediate_results(self, results: Dict[str, List[Dict]]):
        """중간 결과 저장 (API 오류 시 복구용)"""
        try:
            output_file = "smart_extraction_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 중간 결과 저장 실패: {str(e)}")


class ExtractionValidator:
    """추출 결과 검증 및 수정 클래스"""
    
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
    
    def validate_and_correct_mappings(self, results_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """전체 결과 데이터의 매핑을 검증하고 수정"""
        corrected_data = {}
        total_corrections = 0
        
        for folder_name, folder_results in results_data.items():
            print(f"\n📂 {folder_name} 폴더 검증 중...")
            corrected_results, corrections = self._validate_folder_mappings(folder_results)
            corrected_data[folder_name] = corrected_results
            total_corrections += corrections
            
            if corrections > 0:
                print(f"  ✅ {corrections}개 항목 수정됨")
            else:
                print(f"  ✅ 모든 매핑이 정확함")
        
        print(f"\n📊 총 {total_corrections}개 항목이 수정되었습니다.")
        return corrected_data
    
    def _validate_folder_mappings(self, folder_results: List[Dict]) -> tuple[List[Dict], int]:
        """폴더 내 결과들의 매핑을 검증하고 수정"""
        corrected_results = []
        correction_count = 0
        
        # 배치 크기로 나누어 처리 (API 제한 고려)
        batch_size = 10
        
        for i in range(0, len(folder_results), batch_size):
            batch = folder_results[i:i + batch_size]
            corrected_batch, batch_corrections = self._validate_batch(batch)
            corrected_results.extend(corrected_batch)
            correction_count += batch_corrections
        
        return corrected_results, correction_count
    
    def _validate_batch(self, batch: List[Dict]) -> tuple[List[Dict], int]:
        """배치 단위로 검증 및 수정"""
        try:
            # 검증이 필요한 항목들만 필터링
            items_to_validate = []
            items_indices = []
            
            for idx, item in enumerate(batch):
                # 파일명과 현재 매핑이 일치하는지 간단 체크
                filename = item.get('original_filename', '')
                current_artist = item.get('artist')
                current_title = item.get('title')
                
                # 명백히 잘못된 매핑 감지
                if self._needs_validation(filename, current_artist, current_title):
                    items_to_validate.append(item)
                    items_indices.append(idx)
            
            if not items_to_validate:
                return batch, 0
            
            # OpenAI로 올바른 매핑 요청
            corrected_mappings = self._get_corrected_mappings(items_to_validate)
            
            # 결과 적용
            corrected_batch = batch.copy()
            correction_count = 0
            
            for i, mapping in enumerate(corrected_mappings):
                if i < len(items_indices):
                    original_idx = items_indices[i]
                    original_item = corrected_batch[original_idx]
                    
                    # 수정이 필요한지 확인
                    if (mapping.get('artist') != original_item.get('artist') or 
                        mapping.get('title') != original_item.get('title')):
                        
                        # 매핑 업데이트
                        corrected_batch[original_idx].update({
                            'artist': mapping.get('artist'),
                            'title': mapping.get('title'),
                            'confidence': mapping.get('confidence', 'medium'),
                            'final_format': f"{mapping.get('artist')} - {mapping.get('title')}" if mapping.get('artist') else mapping.get('title')
                        })
                        correction_count += 1
                        print(f"    🔧 수정: {original_item['original_filename'][:50]}...")
            
            return corrected_batch, correction_count
            
        except Exception as e:
            print(f"    ⚠️ 배치 검증 오류: {str(e)}")
            return batch, 0
    
    def _needs_validation(self, filename: str, current_artist: str, current_title: str) -> bool:
        """검증이 필요한지 판단"""
        filename_lower = filename.lower()
        
        # artist나 title이 None이거나 비어있으면 검증 필요
        if not current_artist or not current_title:
            return True
        
        # 아티스트명이 파일명에 없는 경우
        if current_artist and current_artist.lower() not in filename_lower:
            return True
        
        # 제목이 파일명에 없는 경우
        if current_title and current_title.lower() not in filename_lower:
            return True
        
        return False
    
    def _get_corrected_mappings(self, items: List[Dict]) -> List[Dict]:
        """OpenAI를 통해 올바른 매핑 정보 획득"""
        filenames_info = []
        for item in items:
            filenames_info.append({
                'filename': item['original_filename'],
                'current_artist': item.get('artist'),
                'current_title': item.get('title')
            })
        
        prompt = f"""다음 K-pop 댄스 커버 영상 파일명들의 아티스트명과 노래 제목을 정확히 추출해주세요.

규칙:
1. 파일명에 명확하게 포함된 아티스트명과 노래 제목만 추출
2. 파일명에 없는 정보는 추론하지 말고 null로 설정
3. 현재 매핑이 잘못되었다면 수정해주세요

파일명 정보:
{json.dumps(filenames_info, ensure_ascii=False, indent=2)}

각 파일명에 대해 다음 JSON 형식으로 응답해주세요:
{{
  "artist": "아티스트명 또는 null",
  "title": "노래 제목 또는 null", 
  "confidence": "high/medium/low"
}}

전체 응답은 JSON 배열 형태로 해주세요."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 K-pop 전문가입니다. 파일명에서 정확한 아티스트와 노래 제목만 추출해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # JSON 블록 추출
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            return json.loads(content)
            
        except Exception as e:
            print(f"    ⚠️ OpenAI API 오류: {str(e)}")
            return [{'artist': None, 'title': None, 'confidence': 'low'} for _ in items]


def main():
    # OpenAI API 키 설정
    api_key = os.getenv('OPENAI_API_KEY')

    
    # config.json에서 choom 폴더 경로 가져오기
    try:
        with open("config/config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        choom_path = config.get('general', {}).get('video_folder_path', '/Users/minsung/Documents/choom')
    except Exception as e:
        print(f"⚠️ config.json 로드 실패, 기본 경로 사용: {e}")
        choom_path = "/Users/minsung/Documents/choom"
    
    # 스마트 추출기 초기화
    extractor = SmartTitleExtractor(api_key)
    
    try:
        # 모든 폴더 처리
        print("choom 폴더 내 모든 하위 폴더를 스캔 중...")
        all_results = extractor.process_choom_folders(choom_path)
        
        # 결과 저장
        output_file = "smart_extraction_results.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        # 요약 출력
        print(f"\n🎉 처리 완료!")
        
        # 기존 폴더와 새로 처리된 폴더 구분
        existing_folders = extractor._load_existing_results()
        new_folders = {k: v for k, v in all_results.items() if k not in existing_folders}
        
        print(f"📁 전체 폴더: {len(all_results)}개")
        print(f"  📋 기존 폴더: {len(existing_folders)}개 (건너뜀)")
        print(f"  🆕 새로 처리된 폴더: {len(new_folders)}개")
        
        total_files = sum(len(files) for files in all_results.values())
        new_files = sum(len(files) for files in new_folders.values())
        
        print(f"📄 총 파일: {total_files}개")
        print(f"  🆕 새로 처리된 파일: {new_files}개")
        
        if new_folders:
            print(f"\n📊 새로 처리된 폴더 상세:")
            for folder_name, results in new_folders.items():
                high_confidence = sum(1 for r in results if r.get('confidence') == 'high')
                print(f"  📂 {folder_name}: {len(results)}개 파일 (고신뢰도: {high_confidence}개)")
        
        print(f"💾 결과 저장: {output_file}")
        
        # 샘플 결과 출력 (새로 처리된 폴더만)
        if new_folders:
            print(f"\n📋 새로 처리된 샘플 결과:")
            first_new_folder = list(new_folders.items())[0]
            folder_name, results = first_new_folder
            for result in results[:3]:  # 처음 3개만
                print(f"  폴더: {folder_name}")
                print(f"  원본: {result['original_filename']}")
                print(f"  결과: {result['final_format']}")
                print(f"  신뢰도: {result['confidence']}")
                print()
        else:
            print(f"\n📋 모든 폴더가 이미 처리되어 새로운 결과가 없습니다.")
        
        # 데이터 매핑 검증 및 수정
        print(f"\n🔍 데이터 매핑 검증 시작...")
        validator = ExtractionValidator(api_key)
        corrected_results = validator.validate_and_correct_mappings(all_results)
        
        if corrected_results != all_results:
            print(f"✅ 매핑 오류 수정 완료! 결과를 다시 저장합니다.")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(corrected_results, f, ensure_ascii=False, indent=2)
        else:
            print(f"✅ 모든 매핑이 정확합니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()