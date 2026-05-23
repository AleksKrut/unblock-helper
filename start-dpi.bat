@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Создаю окружение...
  py -3 -m venv .venv
  call .venv\Scripts\activate.bat
  pip install -r requirements.txt -q
)

:: DPI требует прав администратора (WinDivert)
powershell -NoProfile -Command "Start-Process -FilePath '%~dp0.venv\Scripts\python.exe' -ArgumentList 'main.py','dpi-start','--admin' -Verb RunAs -WorkingDirectory '%~dp0'"
echo.
echo Если появилось окно UAC — нажмите «Да».
pause
