# 고정 도메인 설정 가이드

도메인이 변경되지 않고 고정된 상태로 사용하는 방법들을 소개합니다.

## 🎯 무료 고정 도메인 방법

### 방법 1: Cloudflare Tunnel (최고 추천 ⭐⭐⭐)

**장점:**
- 완전 무료
- HTTPS 자동 제공
- 고정 도메인 가능
- 공인 IP 불필요 (터널링 방식)
- 라우터 설정 불필요

**단점:**
- Cloudflare에 도메인 등록 필요 (무료 도메인 가능)

#### 단계별 설정

##### 1단계: 무료 도메인 얻기 (도메인이 없는 경우)

**옵션 A: Freenom (무료 도메인)**
- https://www.freenom.com 접속
- `.tk`, `.ml`, `.ga`, `.cf` 같은 무료 도메인 등록
- 예: `my-server.tk`, `monitoring.ml`

**옵션 B: 실제 도메인 구매 (연간 $10-15)**
- Namecheap, Google Domains 등에서 구매
- 예: `example.com`

##### 2단계: Cloudflare에 도메인 추가

1. https://dash.cloudflare.com 접속 및 회원가입
2. "Add a Site" 클릭
3. 도메인 입력 (예: `my-server.tk`)
4. 무료 플랜 선택 (Free)
5. DNS 서버 정보 확인 (예: `ns1.cloudflare.com`, `ns2.cloudflare.com`)
6. 도메인 등록업체에서 DNS 서버 변경 (Freenom인 경우 Nameservers 설정)

##### 3단계: cloudflared 설치 및 로그인

```powershell
# cloudflared 다운로드 (이미 있다면 생략)
Invoke-WebRequest -Uri https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe -OutFile cloudflared.exe

# 로그인 (브라우저가 열림)
.\cloudflared.exe tunnel login
```

##### 4단계: 터널 생성

```powershell
# 터널 생성 (my-server는 원하는 이름)
.\cloudflared.exe tunnel create my-server
```

##### 5단계: 도메인 라우팅 설정

```powershell
# DNS 레코드 추가 (서브도메인 생성)
.\cloudflared.exe tunnel route dns my-server your-subdomain.my-server.tk
# 예: .\cloudflared.exe tunnel route dns my-server api.my-server.tk
```

##### 6단계: 설정 파일 생성

`%USERPROFILE%\.cloudflared\config.yml` 파일 생성/수정:

```yaml
tunnel: YOUR_TUNNEL_UUID  # tunnel create 시 생성된 UUID
credentials-file: %USERPROFILE%\.cloudflared\YOUR_TUNNEL_UUID.json

ingress:
  - hostname: your-subdomain.my-server.tk  # 위에서 생성한 서브도메인
    service: http://localhost:8000
  - service: http_status:404
```

##### 7단계: 터널 실행

```powershell
.\cloudflared.exe tunnel run my-server
```

이제 `https://your-subdomain.my-server.tk`로 접속 가능합니다!

---

### 방법 2: DuckDNS (동적 DNS)

**장점:**
- 완전 무료
- 간단한 설정
- 고정 도메인 (예: `my-server.duckdns.org`)

**단점:**
- 공인 IP 필요
- 라우터 포트 포워딩 설정 필요
- IP가 변경되면 자동 업데이트 필요

#### 단계별 설정

##### 1단계: DuckDNS 계정 생성

1. https://www.duckdns.org/ 접속
2. 소셜 로그인 (Google, Reddit 등)으로 회원가입
3. 원하는 서브도메인 입력 (예: `my-server`)
4. 완전한 도메인: `my-server.duckdns.org`

##### 2단계: 공인 IP 확인

```powershell
# 현재 공인 IP 확인
Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing | Select-Object -ExpandProperty Content
```

##### 3단계: 라우터 포트 포워딩 설정

1. 라우터 관리 페이지 접속 (보통 `192.168.1.1` 또는 `192.168.0.1`)
2. "포트 포워딩" 또는 "Port Forwarding" 메뉴 찾기
3. 설정 추가:
   - 외부 포트: 8000 (또는 원하는 포트)
   - 내부 IP: 로컬 PC의 IP (예: `192.168.1.100`)
   - 내부 포트: 8000
   - 프로토콜: TCP

##### 4단계: Windows 방화벽 설정

```powershell
# PowerShell 관리자 권한으로 실행
New-NetFirewallRule -DisplayName "Allow Port 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

##### 5단계: IP 자동 업데이트 스크립트

`update_duckdns.ps1` 파일 생성:

```powershell
# DuckDNS 토큰과 도메인 설정
$token = "YOUR_DUCKDNS_TOKEN"  # DuckDNS 사이트에서 확인
$domain = "my-server"  # 서브도메인 이름

# IP 업데이트
$url = "https://www.duckdns.org/update?domains=$domain&token=$token&ip="
Invoke-WebRequest -Uri $url -UseBasicParsing | Out-Null

Write-Host "DuckDNS IP 업데이트 완료: $domain.duckdns.org"
```

##### 6단계: 작업 스케줄러로 자동 업데이트 설정

1. 작업 스케줄러 실행 (`Win + R` → `taskschd.msc`)
2. "기본 작업 만들기" 클릭
3. 이름: "DuckDNS IP 업데이트"
4. 트리거: "컴퓨터 시작 시" + "매 30분마다"
5. 동작: "프로그램 시작"
6. 프로그램: `powershell.exe`
7. 인수: `-ExecutionPolicy Bypass -File "C:\path\to\update_duckdns.ps1"`

##### 7단계: 서버 실행

```powershell
python unified_server.py
```

이제 `http://my-server.duckdns.org:8000`으로 접속 가능합니다!

---

### 방법 3: No-IP (동적 DNS)

DuckDNS와 유사한 서비스입니다.

1. https://www.noip.com/ 접속 및 회원가입
2. 호스트 이름 생성 (예: `my-server.ddns.net`)
3. 클라이언트 프로그램 다운로드 및 설치
4. 자동으로 IP 업데이트됨

---

## 💰 유료 고정 도메인 방법

### 방법 4: ngrok 유료 플랜

**장점:**
- 매우 간단한 설정
- HTTPS 자동 제공
- 고정 도메인 가능

**단점:**
- 월 $8 비용

#### 설정 방법

1. https://ngrok.com/pricing 접속
2. 유료 플랜 구독 (Starter: $8/월)
3. 대시보드에서 고정 도메인 설정
4. ngrok 실행:

```powershell
ngrok http 8000 --domain=your-fixed-domain.ngrok-free.app
```

---

### 방법 5: 실제 도메인 구매 + DuckDNS

**장점:**
- 완전한 커스텀 도메인
- 전문적인 느낌

**단점:**
- 도메인 비용 (연간 $10-15)

#### 설정 방법

1. Namecheap, Google Domains 등에서 도메인 구매
2. DuckDNS에 도메인 추가 (또는 직접 DNS 관리)
3. A 레코드로 공인 IP 연결
4. IP 변경 시 DuckDNS로 자동 업데이트

---

## 📊 방법 비교

| 방법 | 비용 | 설정 난이도 | 고정 도메인 | 공인 IP 필요 | 추천도 |
|------|------|-------------|-------------|--------------|--------|
| Cloudflare Tunnel | 무료 | ⭐⭐ | ✅ | ❌ | ⭐⭐⭐⭐⭐ |
| DuckDNS | 무료 | ⭐⭐⭐ | ✅ | ✅ | ⭐⭐⭐⭐ |
| No-IP | 무료 | ⭐⭐⭐ | ✅ | ✅ | ⭐⭐⭐ |
| ngrok 유료 | $8/월 | ⭐ | ✅ | ❌ | ⭐⭐⭐⭐ |
| 도메인 구매 | $10-15/년 | ⭐⭐⭐⭐ | ✅ | ✅ | ⭐⭐⭐ |

---

## 🎯 최종 추천

### 1순위: Cloudflare Tunnel
- 무료
- 공인 IP 불필요
- 설정이 비교적 간단
- HTTPS 자동 제공

### 2순위: DuckDNS
- 무료
- 공인 IP와 포트 포워딩만 있으면 됨
- 설정이 직관적

### 3순위: ngrok 유료
- 가장 간단한 설정
- 비용 지불 가능하다면 추천

---

## 🚀 빠른 시작 스크립트

### Cloudflare Tunnel 자동 실행

`start_with_cloudflare_fixed.bat`:

```batch
@echo off
chcp 65001 > nul
echo ========================================
echo  서버 + Cloudflare Tunnel (고정 도메인)
echo ========================================
echo.

REM 서버 시작
echo [1/2] Python 서버 시작...
start "서버" cmd /k "python unified_server.py"
timeout /t 3 /nobreak > nul

REM Cloudflare Tunnel 시작
echo [2/2] Cloudflare Tunnel 시작...
echo 고정 도메인으로 연결됩니다.
echo.

cloudflared tunnel run my-server
```

### DuckDNS IP 업데이트 스크립트

`update_duckdns.ps1` (수정 필요):

```powershell
# 설정 부분 (수정 필요!)
$token = "YOUR_DUCKDNS_TOKEN"  # DuckDNS 사이트에서 확인
$domain = "my-server"  # 서브도메인

# IP 업데이트
$url = "https://www.duckdns.org/update?domains=$domain&token=$token&ip="
try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] DuckDNS IP 업데이트 완료: $domain.duckdns.org" -ForegroundColor Green
} catch {
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] DuckDNS 업데이트 실패: $_" -ForegroundColor Red
}
```

---

## 🔧 문제 해결

### Cloudflare Tunnel

**문제: 도메인이 연결되지 않음**
- DNS 서버 변경이 완료되었는지 확인 (최대 24시간 소요 가능)
- `cloudflared tunnel route dns` 명령이 성공했는지 확인

**문제: 502 오류**
- 로컬 서버가 실행 중인지 확인
- 포트 번호가 올바른지 확인

### DuckDNS

**문제: 접속이 안 됨**
- 공인 IP가 올바른지 확인
- 라우터 포트 포워딩이 올바른지 확인
- Windows 방화벽 설정 확인
- IP 업데이트 스크립트가 실행되었는지 확인

**문제: IP가 자동 업데이트되지 않음**
- 작업 스케줄러 설정 확인
- 토큰이 올바른지 확인

---

## 📝 추가 팁

### HTTPS 강제 (Cloudflare)

Cloudflare Dashboard에서:
1. SSL/TLS → Overview
2. 암호화 모드: "Full" 또는 "Full (strict)" 선택
3. SSL/TLS → Edge Certificates
4. "Always Use HTTPS" 활성화

### 커스텀 포트 사용 (DuckDNS)

포트 8000이 아닌 다른 포트를 사용하려면:
- 라우터에서 해당 포트로 포워딩
- URL에 포트 번호 포함: `http://my-server.duckdns.org:8000`

### 서브도메인 여러 개 사용 (Cloudflare)

여러 서비스를 다른 서브도메인으로 제공:

```yaml
ingress:
  - hostname: api.my-server.tk
    service: http://localhost:8000
  - hostname: admin.my-server.tk
    service: http://localhost:8080
  - service: http_status:404
```

