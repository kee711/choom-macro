import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

def analyze_filename(filename: str) -> Dict[str, str]:
    """파일명에서 아티스트와 제목을 추출하고 before/after 결과를 반환"""
    
    # Before: 원본 파일명
    before = filename
    
    # 파일명 정규화 과정
    name = Path(filename).stem
    
    # 패턴 제거 (괄호, 대괄호 등)
    remove_patterns = [
        r'\[.*?\]',    # [MIRRORED], [MV] 등
        r'\(.*?\)'     # (한글명), (1) 등
    ]
    
    for pattern in remove_patterns:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # 키워드 제거
    remove_keywords = ["Official", "MV", "가사", "lyrics", "커버", "댄스", "cover", "MIRRORED", "dance", "Feat", "feat"]
    
    for kw in remove_keywords:
        name = re.sub(r'\b' + re.escape(kw) + r'\b', '', name, flags=re.IGNORECASE)
    
    # 연속된 공백, 언더스코어, 하이픈을 하나의 공백으로 변환
    name = re.sub(r'[_\-\s]+', ' ', name).strip()
    
    # 제목 추출 패턴들
    patterns = [
        r"(?P<artist>\S+)\s+(?P<title>.+)",                    # "STAYC Bubble"
        r"(?P<artist>.+) - (?P<title>.+)",                     # "아티스트 - 곡명"
        r"\[(?:MV|4K)\] (?P<artist>.+?) _ (?P<title>.+)",      # "[MV] 아티스트 _ 곡명"
        r"(?P<title>.+) - (?P<artist>.+) 가사 lyrics",         # "곡명 - 아티스트 가사 lyrics"
        r"(?P<artist>.+)_(?P<title>.+)_.*"                     # "아티스트_곡명_기타"
    ]
    
    artist = ""
    title = ""
    
    for pattern in patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            artist = match.groupdict().get('artist', '').strip()
            title = match.groupdict().get('title', '').strip()
            break
    
    # After: 정규화된 결과
    if artist and title:
        after = f"{artist} - {title}"
    else:
        after = name  # 추출 실패 시 정리된 파일명만
    
    return {
        "before": before,
        "after": after,
        "artist": artist,
        "title": title
    }

def main():
    # 파일 목록 (실제 폴더에서 가져온 파일들)
    filenames = [
        "HOME SWEET HOME.mp4",
        "J.Tajor - Like I Do dance cover.mp4",
        "[MIRRORED] (여자)아이들((G)I-DLE) - 나는 아픈 건 딱 질색이니까 dance cover.mp4",
        "[MIRRORED] ALLDAY PROJECT - FAMOUS dance cover.mp4",
        "[MIRRORED] ALLDAY PROJECT - WICKED dance cover.mp4",
        "[MIRRORED] BOYNEXTDOOR(보이넥스트도어) - 부모님 관람불가 dance cover.mp4",
        "[MIRRORED] HUNTR X(Kpop Demon Hunters) - Golden dance cover.mp4",
        "[MIRRORED] Hearts2Hearts(하츠투하츠) - STYLE dance cover.mp4",
        "[MIRRORED] ILLIT(아일릿) - Magnetic dance cover.mp4",
        "[MIRRORED] IVE(아이브) - Accendio dance cover.mp4",
        "[MIRRORED] IVE(아이브) - Baddie dance cover.mp4",
        "[MIRRORED] IVE(아이브) - 해야(HEYA) dance cover.mp4",
        "[MIRRORED] JINI(지니) - C'mon (Feat. Aminé) dance cover.mp4",
        "[MIRRORED] KAI(카이) - Wait On Me dance cover.mp4",
        "[MIRRORED] KATSEYE(캣츠아이) - Gnarly dance cover.mp4",
        "[MIRRORED] KATSEYE(캣츠아이) - Touch dance cover.mp4",
        "[MIRRORED] KISS OF LIFE(키스오브라이프) - Sugarcoat (NATTY Solo) dance cover.mp4",
        "[MIRRORED] LE SSERAFIM(르세라핌) - CRAZY dance cover (1).mp4",
        "[MIRRORED] LE SSERAFIM(르세라핌) - CRAZY dance cover.mp4",
        "[MIRRORED] LE SSERAFIM(르세라핌) - EASY dance cover (1).mp4",
        "[MIRRORED] LE SSERAFIM(르세라핌) - EASY dance cover.mp4",
        "[MIRRORED] LE SSERAFIM(르세라핌) - Smart dance cover.mp4",
        "[MIRRORED] NMIXX(엔믹스) - 별별별(See that) dance cover.mp4",
        "[MIRRORED] RIIZE(라이즈) - Memories dance cover.mp4",
        "[MIRRORED] RIIZE(라이즈) - Bag Bad Back dance cover.mp4",
        "[MIRRORED] RIIZE(라이즈) - Fly Up dance cover.mp4",
        "[MIRRORED] RIIZE(라이즈) - Love 119 dance cover.mp4",
        "[MIRRORED] RIIZE(라이즈) - Siren(사이렌) dance cover.mp4",
        "[MIRRORED] STAYC(스테이씨) - Bubble dance cover.mp4",
        "[MIRRORED] Saja Boys(Kpop Demon Hunters) - Soda Pop dance cover.mp4",
        "[MIRRORED] TWS(투어스) - 마음 따라 뛰는 건 멋지지 않아 dance cover.mp4",
        "[MIRRORED] TWS(투어스) - 첫 만남은 계획대로 되지 않아 dance cover.mp4",
        "[MIRRORED] aespa(에스파) - Armageddon dance cover.mp4",
        "[MIRRORED] aespa(에스파) - Dirty Work dance cover (1).mp4",
        "[MIRRORED] aespa(에스파) - Dirty Work dance cover.mp4",
        "[MIRRORED] aespa(에스파) - Supernova dance cover.mp4",
        "[MIRRORED] izna(이즈나) - BEEP dance cover.mp4",
        "[MIRRORED] izna(이즈나) - SIGN dance cover.mp4",
        "[MIRRORED] 마크(MARK) - 1999 dance cover.mp4",
        "[MIRRORED] 비스트(하이라이트) (BEAST X HIGHLIGHT) - 없는 엔딩(Endless Ending) dance cover.mp4",
        "[MIRRORED] 아이유(IU) - 홀씨 dance cover.mp4",
        "[MIRRORED] 청하(CHUNG HA) - EENIE MEENIE (Feat. 홍중(ATEEZ)) dance cover.mp4",
        "[MIRRORED] 태연(TAEYEON) - To. X dance cover.mp4",
        "[MIRRORED] 하이라이트(HIGHLIGHT) - Chains dance cover (1).mp4",
        "[MIRRORED] 하이라이트(HIGHLIGHT) - Chains dance cover.mp4",
        "[MIRRORED] 하이라이트(Highlight) - BODY dance cover.mp4"
    ]
    
    # 각 파일명 분석
    analysis_results = []
    
    for filename in filenames:
        result = analyze_filename(filename)
        analysis_results.append(result)
        print(f"Before: {result['before']}")
        print(f"After:  {result['after']}")
        print(f"Artist: {result['artist']}")
        print(f"Title:  {result['title']}")
        print("-" * 80)
    
    # JSON 파일로 저장
    output_file = "filename_analysis_results.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n분석 결과가 {output_file}에 저장되었습니다.")
    print(f"총 {len(analysis_results)}개 파일 분석 완료")

if __name__ == "__main__":
    main()