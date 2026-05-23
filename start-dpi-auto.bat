@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt -q
)

powershell -NoProfile -Command "Start-Process -FilePath '%~dp0.venv\Scripts\python.exe' -ArgumentList 'main.py','dpi-auto','--admin' -Verb RunAs -WorkingDirectory '%~dp0'"
echo Запущен автоподбор стратегий (от администратора).
pause
