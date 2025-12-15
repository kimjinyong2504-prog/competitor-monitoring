# GitHub 및 Render 배포 가이드

이 가이드는 프로젝트를 GitHub에 업로드하고 Render를 통해 배포하는 방법을 설명합니다.

## 1. GitHub 저장소 생성 및 업로드

### 1.1 Git 초기화 (아직 안 했다면)

```bash
# 프로젝트 디렉토리에서
git init
```

### 1.2 .gitignore 확인

`.gitignore` 파일이 이미 생성되어 있습니다. 다음 항목들이 제외됩니다:
- `__pycache__/`
- `*.pyc`
- `venv/`
- `.env` 파일
- 기타 임시 파일들

### 1.3 파일 추가 및 커밋

```bash
# 모든 파일 추가
git add .

# 커밋
git commit -m "Initial commit: 경쟁사 뉴스 모니터링 시스템"

# 또는 주요 파일만 추가하려면:
git add unified_server.py
git add competitor-monitoring.html
git add 251215/
git add 251215_yuil/
git add 251215_aia/
git add naver_news.py
git add requirements.txt
git add README.md
git add .gitignore
git add render.yaml
git commit -m "Initial commit: 경쟁사 뉴스 모니터링 시스템"
```

### 1.4 GitHub 저장소 생성 및 푸시

1. GitHub.com에 로그인
2. 새 저장소 생성 (New Repository)
   - Repository name: `competitor-monitoring` (또는 원하는 이름)
   - Public 또는 Private 선택
   - README, .gitignore, license는 추가하지 않음 (이미 있음)
3. 저장소 생성 후 표시되는 명령어 실행:

```bash
# 원격 저장소 추가 (YOUR_USERNAME을 실제 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/competitor-monitoring.git

# 브랜치 이름을 main으로 변경 (필요한 경우)
git branch -M main

# 푸시
git push -u origin main
```

## 2. Render 배포

### 2.1 Render 계정 생성

1. https://render.com 접속
2. GitHub 계정으로 로그인 (권장)

### 2.2 새 Web Service 생성

1. Render 대시보드에서 "New +" 클릭
2. "Web Service" 선택
3. GitHub 저장소 연결
   - "Connect account" 또는 "Connect repository" 클릭
   - GitHub 저장소 선택
   - 저장소 연결

### 2.3 서비스 설정

다음 정보를 입력:

- **Name**: `competitor-monitoring` (또는 원하는 이름)
- **Environment**: `Python 3`
- **Region**: 원하는 지역 선택 (Seoul 등)
- **Branch**: `main` (또는 기본 브랜치)
- **Root Directory**: (비워두기 - 루트 디렉토리 사용)
- **Build Command**: 
  ```
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```
  python unified_server.py
  ```

### 2.4 환경 변수 설정 (선택사항)

현재는 네이버 API 키가 코드에 하드코딩되어 있지만, 보안을 위해 환경 변수로 관리할 수 있습니다:

- `NAVER_CLIENT_ID`: 네이버 API 클라이언트 ID
- `NAVER_CLIENT_SECRET`: 네이버 API 클라이언트 시크릿

**참고**: Render는 자동으로 `PORT` 환경 변수를 제공하므로 별도 설정 불필요

### 2.5 배포

1. "Create Web Service" 클릭
2. 배포가 자동으로 시작됩니다
3. 배포 완료 후 제공되는 URL로 접속 가능
   - 예: `https://competitor-monitoring.onrender.com`

## 3. 배포 후 확인

### 3.1 서비스 접속

배포 완료 후 제공된 URL로 접속:
- 메인 대시보드: `https://your-app.onrender.com/competitor-monitoring.html`
- 화승 R&A: `https://your-app.onrender.com/hwasung`
- 유일고무: `https://your-app.onrender.com/yuil`
- AIA: `https://your-app.onrender.com/aia`

### 3.2 로그 확인

Render 대시보드의 "Logs" 탭에서 서버 로그를 확인할 수 있습니다.

### 3.3 문제 해결

**문제**: 서버가 시작되지 않음
- **해결**: Logs 탭에서 오류 메시지 확인
- 포트 설정이 올바른지 확인
- requirements.txt의 패키지가 모두 설치되었는지 확인

**문제**: 404 오류
- **해결**: 경로가 올바른지 확인 (`/competitor-monitoring.html` 등)
- 정적 파일 경로 확인

**문제**: 데이터가 저장되지 않음
- **해결**: Render의 무료 플랜은 영구 저장소가 아닐 수 있습니다
- 데이터베이스나 외부 저장소 사용 고려

## 4. 자동 배포 설정

Render는 기본적으로 GitHub에 푸시할 때마다 자동으로 재배포됩니다.

### 4.1 자동 배포 비활성화 (선택사항)

Settings > Build & Deploy > Auto-Deploy에서 비활성화 가능

### 4.2 수동 배포

필요시 "Manual Deploy" 버튼으로 수동 배포 가능

## 5. 추가 최적화

### 5.1 데이터 영구 저장

Render의 무료 플랜은 파일 시스템이 영구적이지 않을 수 있습니다. 다음을 고려하세요:
- 외부 데이터베이스 사용 (PostgreSQL, MongoDB 등)
- 클라우드 스토리지 사용 (AWS S3, Google Cloud Storage 등)

### 5.2 성능 최적화

- 무료 플랜은 15분간 요청이 없으면 서비스가 sleep 상태가 됩니다
- 첫 요청 시 깨어나는 데 시간이 걸릴 수 있습니다
- 유료 플랜으로 업그레이드하면 항상 활성 상태 유지 가능

## 6. 보안 고려사항

1. **API 키 보안**: 환경 변수로 관리
2. **HTTPS**: Render는 기본적으로 HTTPS 제공
3. **CORS**: 필요시 CORS 설정 추가

## 7. 업데이트 방법

코드를 수정한 후:

```bash
git add .
git commit -m "업데이트 내용 설명"
git push origin main
```

Render가 자동으로 재배포합니다.

## 문제 발생 시

1. Render 대시보드의 Logs 확인
2. GitHub Actions (사용 중인 경우) 확인
3. 로컬에서 테스트 후 배포

