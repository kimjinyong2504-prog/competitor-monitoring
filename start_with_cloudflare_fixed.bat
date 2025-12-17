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
echo.
echo 참고: 고정 도메인으로 연결됩니다.
echo 설정이 완료되지 않았다면 setup_cloudflare_tunnel.ps1을 실행하세요.
echo.

cloudflared tunnel run my-server
pause

