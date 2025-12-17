@echo off
chcp 65001 > nul
echo ========================================
echo  로컬 서버 + Cloudflare Tunnel 시작
echo ========================================
echo.

REM cloudflared 확인
where cloudflared >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [오류] cloudflared가 설치되어 있지 않습니다.
    echo.
    echo 설치 방법:
    echo 1. https://github.com/cloudflare/cloudflared/releases 접속
    echo 2. cloudflared-windows-amd64.exe 다운로드
    echo 3. cloudflared.exe로 이름 변경 후 이 폴더에 복사하거나 PATH에 추가
    echo.
    echo 또는 Chocolatey 사용:
    echo   choco install cloudflared
    echo.
    pause
    exit /b 1
)

REM 서버 시작
echo [1/2] Python 서버를 시작합니다...
start "서버" cmd /k "python unified_server.py"
timeout /t 3 /nobreak > nul

REM Cloudflare Tunnel 시작
echo [2/2] Cloudflare Tunnel을 시작합니다...
echo.
echo 참고: Cloudflare Tunnel은 설정이 필요합니다.
echo 1. cloudflared tunnel login
echo 2. cloudflared tunnel create my-server
echo 3. 설정 파일 작성 (%USERPROFILE%\.cloudflared\config.yml)
echo.
echo 자세한 내용은 DOMAIN_SETUP_GUIDE.md를 참조하세요.
echo.

start "Cloudflare Tunnel" cmd /k "cloudflared tunnel run my-server"
echo.
echo ========================================
echo  서버와 Cloudflare Tunnel이 시작되었습니다.
echo ========================================
echo.
pause

