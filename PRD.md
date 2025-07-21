비밀번호 : test1234!@#$

# 숏폼 영상 자동 업로드 매크로 PRD (Product Requirements Document)

## 1. 프로젝트 개요

**목적**: 로컬 폴더의 숏폼 영상들을 https://app.hanlim.world/upload 사이트에 자동으로 업로드하는 매크로 시스템 구축

**주요 도전과제**: 
- 다양한 형식의 파일명에서 노래 제목 추출
- 한글/영문 노래 제목의 Spotify API 기반 정규화
- 웹사이트 자동화를 통한 업로드 프로세스

## 2. 기능 요구사항

### 2.1 핵심 워크플로우
1. **파일 스캔**: 지정된 폴더에서 영상 파일 목록 수집
2. **제목 추출**: 파일명에서 아티스트 및 곡명 추출
3. **제목 정규화**: Spotify API를 통한 영문 제목 변환/검증
4. **웹 자동화 업로드**:
   - 노래 검색 (class="upload-step-1-search-container")
   - 검색 결과에서 일치하는 노래 선택
   - 다음 버튼 클릭
   - 영상 가져오기 버튼 클릭
   - 파일 선택 및 업로드
   - 설명 입력
   - 최종 업로드 완료

### 2.2 파일명 처리 패턴 지원
```
- "아티스트 - 곡명.mp4"
- "Artist - Song Title (Official MV).mp4"
- "[MV] Artist(아티스트) _ Song Title.mp4"
- "Song Title - Artist 가사 lyrics.mp4"
- "아티스트_곡명_커버_댄스.mp4"
```

## 3. 기술 스택

**주요 라이브러리**:
- `selenium` 또는 `playwright`: 웹 자동화
- `spotipy`: Spotify API 클라이언트
- `fuzzywuzzy`: 문자열 유사도 비교
- `regex`: 고급 정규표현식 처리
- `configparser`: 설정 파일 관리
- `logging`: 로그 관리

**Python 버전**: 3.8+

## 4. 시스템 아키텍처

```
src/
├── main.py                 # 메인 실행 파일
├── modules/
│   ├── file_manager.py     # 파일 시스템 관리
│   ├── title_extractor.py  # 제목 추출 로직
│   ├── spotify_client.py   # Spotify API 연동
│   ├── web_automator.py    # 웹 자동화
│   ├── config_manager.py   # 설정 관리
│   └── logger.py          # 로깅 시스템
├── config/
│   ├── config.json        # 메인 설정
│   ├── artist_mapping.json # 한영 아티스트명 매핑
│   └── title_patterns.json # 파일명 패턴 정의
├── logs/                  # 로그 파일 저장
└── requirements.txt       # 의존성 목록
```

## 5. 사용자 제공 정보

### 5.1 필수 정보
```json
{
  "video_folder_path": "/path/to/video/folder",
  "spotify_credentials": {
    "client_id": "your_spotify_client_id",
    "client_secret": "your_spotify_client_secret"
  },
  "supported_formats": [".mp4", ".avi", ".mov"],
  "upload_description_template": "업로드된 영상입니다. #shorts #music"
}
```

### 5.2 선택적 정보
```json
{
  "artist_mapping": {
    "아이유": "IU",
    "블랙핑크": "BLACKPINK",
    "방탄소년단": "BTS"
  },
  "upload_delay_seconds": 5,
  "max_retries": 3,
  "similarity_threshold": 0.8
}
```

## 6. 설정 파일 구조

### config.json
```json
{
  "general": {
    "video_folder_path": "",
    "log_level": "INFO",
    "max_concurrent_uploads": 1
  },
  "spotify": {
    "client_id": "",
    "client_secret": ""
  },
  "web_automation": {
    "browser": "chrome",
    "headless": false,
    "implicit_wait": 10,
    "upload_timeout": 300
  },
  "title_extraction": {
    "similarity_threshold": 0.8,
    "remove_keywords": ["Official", "MV", "가사", "lyrics", "커버", "댄스"]
  }
}
```

## 7. 에러 처리 방안

### 7.1 예외 상황 및 해결책
- **노래 검색 실패**: 유사도 기반 매칭, 수동 매핑 테이블 활용
- **파일 업로드 실패**: 재시도 로직, 파일 크기/형식 검증
- **웹 요소 찾기 실패**: 대기 시간 증가, CSS 셀렉터 다중화
- **네트워크 오류**: 지수적 백오프 재시도

### 7.2 로깅 전략
```python
# 로그 레벨별 기록
ERROR: 업로드 실패, API 오류
WARNING: 불확실한 매칭, 재시도 발생
INFO: 성공적인 업로드, 진행 상황
DEBUG: 상세한 처리 과정
```

## 8. 개발 단계별 구현 계획

### Phase 1: 기본 구조 구축
- [ ] 프로젝트 구조 생성
- [ ] 설정 파일 관리 시스템
- [ ] 로깅 시스템 구현
- [ ] 파일 스캔 기능

### Phase 2: 제목 처리 시스템
- [ ] 정규표현식 기반 제목 추출
- [ ] Spotify API 연동
- [ ] 한영 매핑 시스템
- [ ] 유사도 비교 로직

### Phase 3: 웹 자동화
- [ ] Selenium/Playwright 설정
- [ ] 노래 검색 자동화
- [ ] 파일 업로드 자동화
- [ ] 전체 워크플로우 통합

### Phase 4: 에러 처리 및 최적화
- [ ] 예외 처리 강화
- [ ] 재시도 로직 구현
- [ ] 성능 최적화
- [ ] 사용자 인터페이스 개선

## 9. 테스트 계획

### 9.1 단위 테스트
- 제목 추출 정확도 테스트
- Spotify API 응답 처리 테스트
- 웹 요소 인식 테스트

### 9.2 통합 테스트
- 전체 워크플로우 테스트
- 다양한 파일명 패턴 테스트
- 에러 시나리오 테스트

### 9.3 테스트 데이터
```
테스트 파일명 예시:
- "아이유 - Love wins all.mp4"
- "BTS (방탄소년단) 'Dynamite' Official MV.mp4"
- "[4K] BLACKPINK - 'Pink Venom' M/V.mp4"
- "NewJeans (뉴진스) 'Get Up' Official Video.mp4"
```

## 10. 사용 가이드

### 10.1 초기 설정
```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. config.json 편집
# 3. Spotify API 키 설정
# 4. 비디오 폴더 경로 설정
```

### 10.2 실행 방법
```bash
python main.py
```

### 10.3 모니터링
- 실시간 로그 출력
- 성공/실패 통계
- 처리된 파일 목록

## 11. 추가 고려사항

### 11.1 성능 최적화
- 배치 처리를 통한 효율성 향상
- 멀티스레딩 지원 (신중한 접근 필요)
- 캐시 시스템으로 중복 API 호출 방지

### 11.2 확장성
- 다른 업로드 사이트 지원을 위한 플러그인 구조
- 웹훅을 통한 외부 시스템 연동
- 클라우드 스토리지 연동

이 PRD를 바탕으로 완전한 매크로 시스템을 구현할 수 있습니다. 각 모듈을 단계별로 개발하고 테스트하면서 안정적인 자동화 도구를 만들 수 있을 것입니다. 