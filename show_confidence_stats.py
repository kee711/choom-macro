#!/usr/bin/env python3
"""
Smart Extraction Results 통계 출력 스크립트
각 폴더별 파일 개수와 confidence 분포를 마크다운 형식으로 출력
"""

import json
from collections import Counter
from pathlib import Path

def show_confidence_stats():
    """confidence별 파일 통계를 마크다운 형식으로 표시"""
    results_file = Path("smart_extraction_results.json")
    
    if not results_file.exists():
        print("❌ smart_extraction_results.json 파일을 찾을 수 없습니다.")
        return
    
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 파일 로드 실패: {str(e)}")
        return
    
    print('# Smart Extraction Results Statistics\n')
    
    total_files = 0
    total_confidence = Counter()
    
    for folder_name, files in data.items():
        folder_count = len(files)
        total_files += folder_count
        
        folder_confidence = Counter(item.get('confidence', 'unknown') for item in files)
        total_confidence.update(folder_confidence)
        
        high = folder_confidence.get('high', 0)
        medium = folder_confidence.get('medium', 0)
        low = folder_confidence.get('low', 0)
        
        print(f'## {folder_name}')
        print(f'- **Total**: {folder_count} files')
        print(f'- **High**: {high} files ({high/folder_count*100:.1f}%)')
        print(f'- **Medium**: {medium} files ({medium/folder_count*100:.1f}%)')
        print(f'- **Low**: {low} files ({low/folder_count*100:.1f}%)')
        print()
    
    print('## Summary')
    print(f'- **Total Folders**: {len(data)}')
    print(f'- **Total Files**: {total_files}')
    print(f'- **High Confidence**: {total_confidence.get("high", 0)} files ({total_confidence.get("high", 0)/total_files*100:.1f}%)')
    print(f'- **Medium Confidence**: {total_confidence.get("medium", 0)} files ({total_confidence.get("medium", 0)/total_files*100:.1f}%)')
    print(f'- **Low Confidence**: {total_confidence.get("low", 0)} files ({total_confidence.get("low", 0)/total_files*100:.1f}%)')

if __name__ == '__main__':
    show_confidence_stats()