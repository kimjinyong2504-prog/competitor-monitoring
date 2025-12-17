@echo off
chcp 65001 > nul
echo ========================================
echo  로컬 서버 + ngrok 터널 시작
echo ========================================
echo.

REM 서버 시작
echo [1/2] Python 서버를 시작합니다...
start "서버" cmd /k "python unified_server.py"
timeout /t 3 /nobreak > nul

REM ngrok 시작
echo [2/2] ngrok 터널을 생성합니다...
echo.
echo 참고: ngrok이 제공하는 URL을 복사하여 사용하세요.
echo (예: https://abc123.ngrok-free.app)
echo.

REM ngrok이 설치되어 있는지 확인
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [오류] ngrok이 설치되어 있지 않습니다.
    echo.
    echo 설치 방법:
    echo 1. https://ngrok.com/ 접속
    echo 2. 회원가입 후 다운로드
    echo 3. ngrok.exe를 이 폴더에 복사하거나 PATH에 추가
    echo.
    pause
    exit /b 1
)

start "Ngrok" cmd /k "ngrok http 8000"
echo.
echo ========================================
echo  서버와 ngrok이 시작되었습니다.
echo  새 창에서 URL을 확인하세요.
echo ========================================
echo.
pause

