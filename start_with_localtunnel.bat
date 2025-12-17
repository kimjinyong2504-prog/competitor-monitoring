@echo off
chcp 65001 > nul
echo ========================================
echo  로컬 서버 + localtunnel 시작
echo ========================================
echo.

REM Node.js 확인
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [오류] Node.js가 설치되어 있지 않습니다.
    echo.
    echo 설치 방법:
    echo 1. https://nodejs.org/ 접속
    echo 2. Node.js 다운로드 및 설치
    echo 3. 설치 후 다시 실행
    echo.
    pause
    exit /b 1
)

REM localtunnel 설치 확인 및 설치
echo [1/3] localtunnel 설치 확인 중...
where lt >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo localtunnel이 설치되어 있지 않습니다. 설치 중...
    call npm install -g localtunnel
    if %ERRORLEVEL% NEQ 0 (
        echo [오류] localtunnel 설치에 실패했습니다.
        pause
        exit /b 1
    )
)

REM 서버 시작
echo [2/3] Python 서버를 시작합니다...
start "서버" cmd /k "python unified_server.py"
timeout /t 3 /nobreak > nul

REM localtunnel 시작
echo [3/3] localtunnel 터널을 생성합니다...
echo.
echo 참고: localtunnel이 제공하는 URL을 복사하여 사용하세요.
echo (예: https://my-server.loca.lt)
echo.

start "Localtunnel" cmd /k "lt --port 8000"
echo.
echo ========================================
echo  서버와 localtunnel이 시작되었습니다.
echo  새 창에서 URL을 확인하세요.
echo ========================================
echo.
pause

