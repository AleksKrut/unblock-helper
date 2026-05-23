@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Создание окружения...
  py -3 -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements-desktop.txt -q
) else (
  call .venv\Scripts\activate.bat
)

:: DPI требует прав администратора
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Запрос прав администратора...
  powershell -NoProfile -Command "Start-Process -FilePath '%~dp0.venv\Scripts\pythonw.exe' -ArgumentList 'desktop\app.py' -Verb RunAs -WorkingDirectory '%~dp0'"
  exit /b
)

start "" "%~dp0.venv\Scripts\pythonw.exe" desktop\app.py
