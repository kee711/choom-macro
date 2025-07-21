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
{chr(10).join([f"{i+1}. {name}" for i, name in enumerate(cleaned_names)])}

각 파일명에 대해 다음 JSON 형식으로 응답해주세요:
{{
  "artist": "아티스트명 또는 null",
  "title": "노래 제목",
  "confidence": "high/medium/low"
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
            
            # 결과와 원본 파일명 매칭
            final_results = []
            for i, (original_filename, result) in enumerate(zip(filenames, results)):
                final_results.append({
                    "folder": "",  # 나중에 설정
                    "original_filename": original_filename,
                    "cleaned_filename": cleaned_names[i],
                    "artist": result.get("artist"),
                    "title": result.get("title", ""),
                    "confidence": result.get("confidence", "medium"),
                    "final_format": f"{result.get('artist', '')} - {result.get('title', '')}" if result.get('artist') else result.get('title', '')
                })
            
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
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()