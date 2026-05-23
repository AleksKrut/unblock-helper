@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Создание окружения...
  py -3 -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt -q
) else (
  call .venv\Scripts\activate.bat
)

python main.py menu
pause
