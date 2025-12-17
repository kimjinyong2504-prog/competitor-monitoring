# GitHub 및 Render 설정 가이드

## 1단계: GitHub 저장소 생성

### 1.1 새 저장소 만들기

1. GitHub 메인 페이지에서 우측 상단의 **"+"** 버튼 클릭
2. **"New repository"** 선택

### 1.2 저장소 정보 입력

다음 정보를 입력하세요:

- **Repository name**: `competitor-monitoring` (또는 원하는 이름)
- **Description**: `경쟁사 뉴스 모니터링 시스템 - 화승 R&A, 유일고무, AIA 실시간 뉴스 크롤링`
- **Public** 또는 **Private** 선택 (Public이면 누구나 볼 수 있음)
- ⚠️ **중요**: 아래 항목들은 체크하지 마세요!
  - ❌ Add a README file (이미 있음)
  - ❌ Add .gitignore (이미 있음)
  - ❌ Choose a license (선택사항)

3. **"Create repository"** 버튼 클릭

### 1.3 저장소 URL 확인

저장소가 생성되면 다음과 같은 페이지가 나타납니다:
- 페이지 상단에 저장소 URL이 표시됩니다
- 예: `https://github.com/YOUR_USERNAME/competitor-monitoring`

이 URL을 복사해두세요!

---

## 2단계: 로컬 프로젝트를 GitHub에 업로드

### 2.1 터미널에서 명령어 실행

프로젝트 폴더(`C:\Users\kim.jin.yong\Desktop\251128`)에서 다음 명령어를 실행하세요:

```bash
# 원격 저장소 추가 (YOUR_USERNAME을 실제 GitHub 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/competitor-monitoring.git

# 브랜치 이름을 main으로 변경
git branch -M main

# GitHub에 푸시
git push -u origin main
```

### 2.2 인증

- 첫 푸시 시 GitHub 로그인 창이 나타날 수 있습니다
- GitHub 계정으로 로그인하거나 Personal Access Token을 사용하세요

### 2.3 업로드 확인

GitHub 저장소 페이지를 새로고침하면 파일들이 업로드된 것을 확인할 수 있습니다.

---

## 3단계: Render 계정 생성 및 연결

### 3.1 Render 가입

1. https://render.com 접속
2. **"Get Started for Free"** 클릭
3. **"Sign up with GitHub"** 선택 (권장)
4. GitHub 계정으로 로그인 및 권한 승인

### 3.2 새 Web Service 생성

1. Render 대시보드에서 **"New +"** 버튼 클릭
2. **"Web Service"** 선택

### 3.3 GitHub 저장소 연결

1. **"Connect account"** 또는 **"Connect repository"** 클릭
2. GitHub 저장소 목록에서 방금 생성한 `competitor-monitoring` 저장소 선택
3. **"Connect"** 클릭

---

## 4단계: Render 서비스 설정

### 4.1 기본 정보 입력

- **Name**: `competitor-monitoring` (또는 원하는 이름)
- **Region**: `Seoul (South Korea)` 또는 가장 가까운 지역 선택
- **Branch**: `main` (기본값)

### 4.2 빌드 및 시작 명령어 설정

- **Environment**: `Python 3` 선택
- **Build Command**: 
  ```
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```
  python unified_server.py
  ```

### 4.3 환경 변수 설정 (선택사항)

현재는 네이버 API 키가 코드에 포함되어 있지만, 보안을 위해 환경 변수로 관리할 수 있습니다:

**"Advanced"** 섹션에서 **"Add Environment Variable"** 클릭:
- Key: `NAVER_CLIENT_ID`
- Value: `00q938ugMTSfuzjWuLk4`
- Key: `NAVER_CLIENT_SECRET`  
- Value: `MrIG7TWaGW`

⚠️ **참고**: Render는 자동으로 `PORT` 환경 변수를 제공하므로 별도 설정 불필요

### 4.4 서비스 생성

1. 모든 설정 확인
2. **"Create Web Service"** 버튼 클릭

---

## 5단계: 배포 대기 및 확인

### 5.1 배포 진행 상황 확인

- Render 대시보드에서 배포 진행 상황을 실시간으로 확인할 수 있습니다
- 첫 배포는 보통 2-5분 정도 소요됩니다

### 5.2 배포 완료 확인

배포가 완료되면:
- **"Live"** 상태로 변경됩니다
- 상단에 서비스 URL이 표시됩니다
- 예: `https://competitor-monitoring.onrender.com`

### 5.3 서비스 접속 테스트

브라우저에서 다음 URL로 접속해보세요:

- 메인 대시보드: `https://your-app.onrender.com/competitor-monitoring.html`
- 화승 R&A: `https://your-app.onrender.com/hwasung`
- 유일고무: `https://your-app.onrender.com/yuil`
- AIA: `https://your-app.onrender.com/aia`

---

## 6단계: 문제 해결

### 6.1 배포 실패 시

1. Render 대시보드의 **"Logs"** 탭 확인
2. 오류 메시지 확인:
   - 패키지 설치 오류: `requirements.txt` 확인
   - 포트 오류: `unified_server.py`의 PORT 설정 확인
   - 경로 오류: 파일 경로 확인

### 6.2 로그 확인 방법

- Render 대시보드 → 서비스 선택 → **"Logs"** 탭
- 실시간 로그와 배포 로그를 확인할 수 있습니다

### 6.3 자주 발생하는 문제

**문제**: "Module not found"
- **해결**: `requirements.txt`에 누락된 패키지 추가

**문제**: "Port already in use"
- **해결**: `unified_server.py`가 PORT 환경 변수를 올바르게 사용하는지 확인

**문제**: "404 Not Found"
- **해결**: 경로가 올바른지 확인 (`/competitor-monitoring.html` 등)

---

## 7단계: 자동 배포 설정 (기본 활성화됨)

### 7.1 자동 배포 확인

Render는 기본적으로 GitHub에 푸시할 때마다 자동으로 재배포됩니다.

### 7.2 수동 배포

필요시:
1. Render 대시보드 → 서비스 선택
2. **"Manual Deploy"** → **"Deploy latest commit"** 클릭

### 7.3 코드 업데이트 방법

코드를 수정한 후:

```bash
git add .
git commit -m "업데이트 내용 설명"
git push origin main
```

Render가 자동으로 재배포를 시작합니다.

---

## 8단계: 무료 플랜 제한사항

### 8.1 Sleep 모드

- Render 무료 플랜은 **15분간 요청이 없으면 서비스가 sleep 상태**가 됩니다
- 첫 요청 시 깨어나는 데 **30초~1분** 정도 소요될 수 있습니다
- 유료 플랜으로 업그레이드하면 항상 활성 상태 유지 가능

### 8.2 데이터 저장

- 무료 플랜의 파일 시스템은 **영구적이지 않을 수 있습니다**
- 서비스 재시작 시 데이터가 초기화될 수 있습니다
- 영구 저장이 필요하면 외부 데이터베이스 사용 권장

---

## 완료!

이제 전 세계 어디서나 접속 가능한 웹 서비스가 완성되었습니다! 🎉

