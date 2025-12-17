# 화승알앤에이 분석 보고서 실행 가이드

## 빠른 시작

### 1. 기본 실행 (가장 간단)

```bash
python main.py
```

이 명령어로 다음이 실행됩니다:
- 화승알앤에이(고유번호: 378850) 정보 수집
- 네이버 뉴스 기사 수집
- HTML 보고서 생성 (`hwasung_rna_report.html`)

---

## DART API 접근 문제 해결

### 문제: DART API 타임아웃 또는 접근 불가

회사 네트워크/방화벽으로 인해 DART API 접근이 차단될 수 있습니다.

### 해결 방법

#### 방법 1: 프록시 설정 (회사 네트워크 사용 시)

**Windows PowerShell:**
```powershell
# 프록시 설정
$env:HTTP_PROXY="http://프록시주소:포트"
$env:HTTPS_PROXY="http://프록시주소:포트"
$env:USE_PROXY="true"

# 실행
python main.py
```

**Windows CMD:**
```cmd
set HTTP_PROXY=http://프록시주소:포트
set HTTPS_PROXY=http://프록시주소:포트
set USE_PROXY=true
python main.py
```

**프록시 주소 확인 방법:**
- IT 부서에 문의
- Windows 설정 > 네트워크 > 프록시 설정 확인
- 브라우저 설정에서 프록시 정보 확인

#### 방법 2: 프록시 설정 도우미 사용

```bash
python setup_proxy.py
```

이 스크립트가 프록시 설정을 안내합니다.

#### 방법 3: 네트워크 환경 변경

- 개인 네트워크(집, 모바일 핫스팟)에서 실행
- VPN 사용
- IT 부서에 방화벽 예외 요청 (opendart.fss.or.kr)

#### 방법 4: 타임아웃 시간 조정

코드에서 타임아웃 시간을 더 늘릴 수 있습니다 (`dart_api.py`의 `timeout=60` 부분).

---

## 실행 옵션

### 자동 업데이트 모드 (1시간마다)

```bash
python main.py --watch
```

### 커스텀 업데이트 간격

```bash
# 30분마다 업데이트
python main.py --watch --interval 1800

# 10분마다 업데이트
python main.py --watch --interval 600
```

### 다른 기업 분석

```bash
python main.py --company "기업명" --corp-code "고유번호"
```

---

## 출력 파일

실행 후 다음 파일들이 생성됩니다:

1. **hwasung_rna_report.html** - HTML 보고서 (브라우저에서 열기)
2. **hwasung_rna_data.json** - 수집된 데이터 (JSON 형식)

---

## 문제 해결

### 네이버 뉴스는 수집되지만 DART 데이터는 안 되는 경우

- 네트워크/방화벽 문제일 가능성이 높습니다
- 위의 프록시 설정 방법을 시도하세요
- 네이버 뉴스 데이터만으로도 보고서가 생성됩니다

### 모든 API가 실패하는 경우

- 인터넷 연결 확인
- 방화벽 설정 확인
- IT 부서에 문의

### 기타 문제

- `requirements.txt`의 패키지가 설치되었는지 확인: `pip install -r requirements.txt`
- Python 버전 확인 (Python 3.7 이상 권장)

---

## 예제

### 예제 1: 기본 실행
```bash
python main.py
```

### 예제 2: 프록시 설정 후 실행
```powershell
$env:HTTP_PROXY="http://proxy.company.com:8080"
$env:HTTPS_PROXY="http://proxy.company.com:8080"
$env:USE_PROXY="true"
python main.py
```

### 예제 3: 자동 업데이트 (30분마다)
```bash
python main.py --watch --interval 1800
```

---

## 참고

- DART API는 하루 호출 제한이 있을 수 있습니다
- 네이버 뉴스 API는 하루 최대 25,000건 요청 가능
- 네트워크가 불안정한 경우 재시도 로직이 자동으로 작동합니다

