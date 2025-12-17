# 로컬 서버 도메인 연결 가이드

로컬 PC에서 실행 중인 서버에 도메인을 연결하는 여러 방법을 소개합니다.

## 방법 1: ngrok (추천 ⭐)

가장 간단하고 빠르게 사용할 수 있는 방법입니다.

### 설치 및 사용

1. **ngrok 다운로드**
   - https://ngrok.com/ 접속
   - 회원가입 후 다운로드
   - 또는 PowerShell에서:
   ```powershell
   # Chocolatey를 사용하는 경우
   choco install ngrok
   
   # 또는 직접 다운로드
   Invoke-WebRequest -Uri https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip -OutFile ngrok.zip
   Expand-Archive ngrok.zip
   ```

2. **ngrok 인증 (무료 플랜)**
   ```powershell
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   # YOUR_AUTH_TOKEN은 ngrok 대시보드에서 확인 가능
   ```

3. **서버 실행 및 ngrok 터널 생성**
   ```powershell
   # 터미널 1: 서버 실행
   python unified_server.py
   
   # 터미널 2: ngrok 터널 생성 (기본 포트 8000)
   ngrok http 8000
   ```

4. **접속**
   - ngrok이 제공하는 URL (예: `https://abc123.ngrok-free.app`)로 접속
   - 무료 플랜은 매번 재시작 시 URL이 변경됩니다
   - 유료 플랜을 사용하면 고정 도메인 사용 가능

### ngrok을 통합한 실행 스크립트

```powershell
# start_with_ngrok.ps1
Start-Process python -ArgumentList "unified_server.py"
Start-Sleep -Seconds 3
Start-Process ngrok -ArgumentList "http 8000"
```

---

## 방법 2: Cloudflare Tunnel (cloudflared) ⭐⭐

Cloudflare의 무료 터널링 서비스로, 무료로 고정 도메인을 사용할 수 있습니다.

### 설치 및 사용

1. **cloudflared 다운로드**
   ```powershell
   # Chocolatey 사용
   choco install cloudflared
   
   # 또는 직접 다운로드
   Invoke-WebRequest -Uri https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe -OutFile cloudflared.exe
   ```

2. **로그인 및 도메인 생성**
   ```powershell
   cloudflared tunnel login
   cloudflared tunnel create my-server
   ```

3. **설정 파일 생성**
   - `%USERPROFILE%\.cloudflared\config.yml` 생성:
   ```yaml
   tunnel: TUNNEL_UUID
   credentials-file: %USERPROFILE%\.cloudflared\TUNNEL_UUID.json
   
   ingress:
     - hostname: your-domain.your-domain.com  # Cloudflare에 등록된 도메인 필요
       service: http://localhost:8000
     - service: http_status:404
   ```

4. **터널 실행**
   ```powershell
   cloudflared tunnel run my-server
   ```

---

## 방법 3: localtunnel (가장 간단)

설정이 거의 필요 없는 방법입니다.

### 설치 및 사용

1. **Node.js 설치 필요** (npm 사용)

2. **localtunnel 설치**
   ```powershell
   npm install -g localtunnel
   ```

3. **터널 생성**
   ```powershell
   # 서버 실행 중인 상태에서
   lt --port 8000 --subdomain my-server
   # 또는 랜덤 서브도메인 사용
   lt --port 8000
   ```

4. **접속**
   - 제공된 URL (예: `https://my-server.loca.lt`)로 접속

---

## 방법 4: DuckDNS (동적 DNS) - 공인 IP 필요

집에 공인 IP가 있고, 포트 포워딩이 가능한 경우 사용 가능합니다.

### 설정 방법

1. **DuckDNS 계정 생성**
   - https://www.duckdns.org/ 접속 및 회원가입
   - 무료 도메인 생성 (예: `my-server.duckdns.org`)

2. **포트 포워딩 설정**
   - 라우터 관리 페이지 접속
   - 포트 8000을 로컬 PC의 내부 IP로 포워딩

3. **IP 업데이트 스크립트 (선택사항)**
   - DuckDNS는 IP 변경 시 자동 업데이트가 가능하지만, Windows에서 업데이트 스크립트 실행 가능

---

## 방법 5: VPS를 프록시로 사용

VPS를 중간 프록시로 사용하여 도메인을 연결하는 방법입니다.

### 구성

```
인터넷 → 도메인 (VPS) → ngrok/cloudflared → 로컬 PC
```

1. VPS에 nginx 설치
2. 도메인을 VPS에 연결
3. VPS에서 ngrok/cloudflared로 로컬 PC와 연결
4. nginx 리버스 프록시 설정

---

## 각 방법 비교

| 방법 | 난이도 | 비용 | 고정 도메인 | 설정 시간 |
|------|--------|------|-------------|-----------|
| ngrok (무료) | ⭐ | 무료 | ❌ (변경됨) | 5분 |
| ngrok (유료) | ⭐ | $8/월 | ✅ | 5분 |
| Cloudflare Tunnel | ⭐⭐ | 무료 | ✅ (도메인 필요) | 30분 |
| localtunnel | ⭐ | 무료 | ❌ (변경됨) | 2분 |
| DuckDNS | ⭐⭐⭐ | 무료 | ✅ | 1시간 |
| VPS 프록시 | ⭐⭐⭐⭐ | VPS 비용 | ✅ | 2시간 |

---

## 추천 설정

### 빠른 테스트용: localtunnel
```powershell
# 가장 빠르게 시작
npm install -g localtunnel
python unified_server.py
# 새 터미널
lt --port 8000
```

### 프로덕션용 (고정 도메인 필요)
- **무료로 고정 도메인**: Cloudflare Tunnel ⭐⭐⭐ (가장 추천)
  - 자세한 설정: `FIXED_DOMAIN_SETUP_GUIDE.md` 참조
  - 자동 설정: `setup_cloudflare_tunnel.ps1` 실행
- **유료 옵션**: ngrok 유료 플랜 ($8/월)
- **공인 IP 있는 경우**: DuckDNS (무료)
  - 자동 IP 업데이트: `update_duckdns.ps1` 사용

---

## 보안 고려사항

1. **HTTPS 사용**: ngrok, Cloudflare Tunnel, localtunnel은 모두 HTTPS 제공
2. **인증 추가**: 프로덕션 환경에서는 API 키나 인증 토큰 추가 권장
3. **방화벽**: 로컬 방화벽에서 불필요한 포트 차단
4. **CORS 설정**: 현재 `unified_server.py`는 CORS를 `*`로 설정했으므로 보안 고려 필요

---

## 스크립트 예제

### ngrok 자동 시작 스크립트 (`start_server_with_ngrok.bat`)

```batch
@echo off
echo 서버를 시작합니다...
start "Server" python unified_server.py
timeout /t 3 /nobreak > nul
echo ngrok 터널을 생성합니다...
start "Ngrok" ngrok http 8000
echo 서버와 ngrok이 시작되었습니다.
pause
```

### cloudflared 자동 시작 스크립트 (`start_server_with_cloudflare.bat`)

```batch
@echo off
echo 서버를 시작합니다...
start "Server" python unified_server.py
timeout /t 3 /nobreak > nul
echo Cloudflare 터널을 시작합니다...
cloudflared tunnel run my-server
pause
```

---

## 문제 해결

### 포트 충돌
- 서버가 다른 포트에서 실행 중인지 확인
- `netstat -ano | findstr :8000`으로 포트 사용 확인

### 연결 오류
- 방화벽 설정 확인
- ngrok/cloudflared 로그 확인

### 느린 응답
- 터널링 서비스는 추가 지연이 발생할 수 있음
- 로컬 네트워크에서는 직접 IP 사용 권장

