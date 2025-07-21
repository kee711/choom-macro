# Auto-Retry 기능 사용법

## 개요
`run_with_retry.py`는 main.py 실행 중 실패가 발생했을 때 자동으로 재시작하는 래퍼 스크립트입니다.

## 사용법

### 기본 실행 (기본값: 최대 10회 재시도, 10초 간격)
```bash
python run_with_retry.py 1-10
```

## Title - AI Parser
```bash
python smart_title_extractor.py
```

## Title - Status
```bash
python show_confidence_stats.py
```

### 커스텀 설정으로 실행
```bash
# 최대 5회 재시도, 30초 간격
python run_with_retry.py --max-retries 5 --retry-delay 30

# 최대 20회 재시도, 5초 간격  
python run_with_retry.py --max-retries 20 --retry-delay 5
```

### 옵션 설명
- `--max-retries`: 최대 재시도 횟수 (기본값: 10)
- `--retry-delay`: 재시도 간격(초) (기본값: 10)

## 동작 방식

1. **main.py 실행**: 스크립트가 main.py를 실행합니다
2. **실패 감지**: main.py가 0이 아닌 exit code로 종료되면 실패로 간주
3. **재시작 대기**: 설정된 시간만큼 대기
4. **자동 재시작**: main.py를 다시 실행
5. **반복**: 성공하거나 최대 재시도 횟수에 도달할 때까지 반복

## 로그

- **콘솔**: 실시간으로 진행 상황 표시
- **파일**: `logs/retry.log`에 재시작 로직 관련 로그 저장
- **main.py 로그**: 기존과 동일하게 `logs/app.log`에 저장

## 실패 처리 개선사항

### main.py 내부 개선
- 업로드 실패 시 개별 에러 처리
- 심각한 브라우저 오류(stale element, session 오류) 발생 시 해당 계정 건너뛰기
- 명확한 exit code 반환 (성공: 0, 실패: 1)

### 자동 재시작 조건
- **업로드 실패**: 개별 파일 업로드가 실패하면 즉시 재시작
- **로그인 실패**: 계정 로그인이 실패하면 즉시 재시작  
- **브라우저 크래시**: 브라우저 세션 오류 시 즉시 재시작
- **네트워크 연결 오류**: 연결 문제 발생 시 재시작
- **기타 예상치 못한 오류**: Exception 발생 시 재시작

### 빠른 재시작의 장점
- 실패 후 빠른 복구 (10초 대기)
- 브라우저 세션을 새로 시작하여 메모리 정리
- 네트워크 연결 상태 리셋
- 더 높은 성공률

## 수동 중단
실행 중 `Ctrl+C`를 누르면 현재 실행을 중단하고 재시작하지 않습니다.

## 예시 출력
```
2025-07-20 03:15:00 - RETRY - INFO - 🚀 Starting auto-retry wrapper for main.py
2025-07-20 03:15:00 - RETRY - INFO - 📊 Max retries: 10, Retry delay: 10s
2025-07-20 03:15:00 - RETRY - INFO - ▶️ Starting main.py (attempt 1)
[main.py 로그들...]
2025-07-20 03:16:30 - main - ERROR - ❌ Failed to upload video.mp4 for account@example.com
2025-07-20 03:16:30 - main - ERROR - 🔄 Upload failed - triggering restart to retry with fresh browser session
2025-07-20 03:16:30 - RETRY - ERROR - ❌ main.py failed with exit code: 1
2025-07-20 03:16:30 - RETRY - WARNING - 🔄 main.py failed, preparing retry 1/10
2025-07-20 03:16:30 - RETRY - INFO - ⏳ Waiting 10 seconds before restart...
2025-07-20 03:16:40 - RETRY - INFO - 🔄 Retry attempt 1/10
2025-07-20 03:16:40 - RETRY - INFO - ▶️ Starting main.py (attempt 2)
[...]
```