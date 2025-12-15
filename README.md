# 경쟁사 뉴스 모니터링 시스템

실시간으로 경쟁사 뉴스를 수집하고 모니터링하는 웹 애플리케이션입니다.

## 주요 기능

- **실시간 뉴스 크롤링**: 네이버 뉴스 API와 구글 뉴스 RSS를 통한 자동 뉴스 수집
- **다중 경쟁사 지원**: 화승 R&A, 유일고무, AIA(아이아) 등 여러 경쟁사 동시 모니터링
- **자동 업데이트**: 1시간마다 자동으로 최신 뉴스 수집
- **수동 새로고침**: 필요시 즉시 뉴스 업데이트 가능
- **기사 상세 보기**: 클릭 시 전체 기사 내용 확인
- **기사 삭제 기능**: 불필요한 기사 삭제 및 재수집 방지
- **반응형 디자인**: 모바일 및 데스크톱 환경 지원

## 기술 스택

- **Backend**: Python 3.13
- **Web Server**: Python http.server
- **Libraries**: 
  - requests: HTTP 요청
  - beautifulsoup4: HTML 파싱
  - feedparser: RSS 피드 파싱
  - urllib3: URL 처리

## 프로젝트 구조

```
.
├── unified_server.py          # 통합 웹 서버
├── competitor-monitoring.html  # 메인 대시보드
├── 251215/                    # 화승 R&A
│   ├── index.html
│   ├── crawler.py
│   ├── scheduler.py
│   └── data.json
├── 251215_yuil/               # 유일고무
│   ├── index.html
│   ├── crawler.py
│   ├── scheduler.py
│   └── data.json
├── 251215_aia/                # AIA(아이아)
│   ├── index.html
│   ├── crawler.py
│   ├── scheduler.py
│   └── data.json
└── naver_news.py              # 네이버 뉴스 API 클라이언트
```

## 설치 및 실행

### 로컬 환경

1. 저장소 클론
```bash
git clone <repository-url>
cd 251128
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
- 네이버 API 클라이언트 ID와 시크릿이 `crawler.py` 파일에 하드코딩되어 있습니다.
- 보안을 위해 환경 변수로 관리하는 것을 권장합니다.

4. 서버 실행
```bash
python unified_server.py
```

5. 브라우저에서 접속
- 메인 대시보드: `http://localhost:8000/competitor-monitoring.html`
- 화승 R&A: `http://localhost:8000/hwasung`
- 유일고무: `http://localhost:8000/yuil`
- AIA: `http://localhost:8000/aia`

## Render 배포

### Render 설정

1. **Web Service 생성**
   - Service Type: Web Service
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python unified_server.py`
   - Environment: Python 3

2. **환경 변수 설정** (선택사항)
   - `NAVER_CLIENT_ID`: 네이버 API 클라이언트 ID
   - `NAVER_CLIENT_SECRET`: 네이버 API 클라이언트 시크릿

3. **포트 설정**
   - Render는 자동으로 `PORT` 환경 변수를 제공합니다.
   - `unified_server.py`가 이를 감지하도록 수정이 필요할 수 있습니다.

## API 엔드포인트

- `GET /competitor-monitoring.html`: 메인 대시보드
- `GET /hwasung`: 화승 R&A 모니터링 페이지
- `GET /yuil`: 유일고무 모니터링 페이지
- `GET /aia`: AIA 모니터링 페이지
- `POST /api/update/{company}`: 뉴스 수동 업데이트
- `POST /api/article/{company}`: 기사 전체 내용 가져오기
- `POST /api/delete/{company}`: 기사 삭제

## 주의사항

- 네이버 API 사용량 제한에 주의하세요.
- 데이터 파일(`data.json`)은 서버 재시작 시 유지되지만, Render의 무료 플랜에서는 영구 저장소가 아닐 수 있습니다.
- SSL 인증서 검증을 비활성화하고 있으므로, 프로덕션 환경에서는 보안을 고려해야 합니다.

## 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.
