@echo off
chcp 65001 >nul
echo PDF to HTML Report Generator - GUI 모드
echo.
python pdf_analyzer_gui.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 오류가 발생했습니다.
    pause
)











