@echo off
chcp 65001 >nul
echo ========================================
echo PDF to HTML Report Generator
echo ========================================
echo.

REM 인자가 있으면 명령줄 모드, 없으면 GUI 모드
if "%~1"=="" (
    echo GUI 모드로 실행합니다...
    echo.
    python pdf_analyzer_gui.py
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo 오류가 발생했습니다.
        pause
    )
    exit /b
)

REM 명령줄 모드
set PDF_FILE=%~1
set OUTPUT_FILE=%~n1_report.html

echo PDF 파일: %PDF_FILE%
echo 출력 파일: %OUTPUT_FILE%
echo.

python pdf_to_html_report.py "%PDF_FILE%" -o "%OUTPUT_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 보고서 생성 완료!
    echo ========================================
    echo 파일: %OUTPUT_FILE%
    echo.
    echo 브라우저에서 열어서 확인하세요.
    echo.
    start "" "%OUTPUT_FILE%"
) else (
    echo.
    echo 오류가 발생했습니다.
)

pause

