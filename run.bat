@echo off
title PortDetector v2.0.0
cd /d "%~dp0"
python main.py %*
if errorlevel 1 (
    echo.
    echo [ERROR] PortDetector failed to start.
    echo Check that PySide6 and pyqtgraph are installed:
    echo   pip install PySide6 pyqtgraph psutil
    echo.
    pause
)
