@echo off
title Vietnam Stock Tracker
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [Loi] Chua tim thay moi truong ao .venv!
    echo Vui long chay setup_and_run.bat truoc de cai dat ban dau.
    echo.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
streamlit run app.py

pause
