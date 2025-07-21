#!/usr/bin/env python3
"""
Smart Extraction Results 매핑 수정 스크립트
잘못 매핑된 아티스트명과 제목을 OpenAI API로 검증하고 수정합니다.
"""

import json
import os
from pathlib import Path
from typing import Dict, List
import openai
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()


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
    """메인 함수"""
    # OpenAI API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   .env 파일에 OPENAI_API_KEY=your_api_key 를 추가해주세요.")
        return
    
    # smart_extraction_results.json 파일 로드
    results_file = Path("smart_extraction_results.json")
    
    if not results_file.exists():
        print("❌ smart_extraction_results.json 파일을 찾을 수 없습니다.")
        return
    
    try:
        with results_file.open('r', encoding='utf-8') as f:
            original_results = json.load(f)
        
        print(f"📋 {len(original_results)}개 폴더의 매핑 데이터를 검증합니다...")
        
        # 검증 및 수정 실행
        validator = ExtractionValidator(api_key)
        corrected_results = validator.validate_and_correct_mappings(original_results)
        
        # 변경사항이 있는 경우에만 저장
        if corrected_results != original_results:
            # 백업 파일 생성
            backup_file = "smart_extraction_results_backup.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(original_results, f, ensure_ascii=False, indent=2)
            print(f"📦 원본 파일을 {backup_file}로 백업했습니다.")
            
            # 수정된 결과 저장
            with results_file.open('w', encoding='utf-8') as f:
                json.dump(corrected_results, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 수정된 결과를 {results_file}에 저장했습니다.")
        else:
            print(f"✅ 모든 매핑이 정확하여 수정할 내용이 없습니다.")
    
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")


if __name__ == "__main__":
    main()