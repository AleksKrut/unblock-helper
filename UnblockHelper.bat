@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "ROOT=%~dp0"
set "EXE=%ROOT%dist\UnblockHelper\UnblockHelper.exe"
set "WORKDIR=%ROOT%dist\UnblockHelper"
set "PY=%ROOT%.venv\Scripts\python.exe"
set "APP=%ROOT%desktop\app.py"

if /I "%~1"=="build" goto build
if /I "%~1"=="cli" goto cli
if /I "%~1"=="kill" goto kill
goto run

:build
echo === Сборка UnblockHelper.exe ===
if not exist "%PY%" (
  py -3 -m venv "%ROOT%.venv"
  "%ROOT%.venv\Scripts\pip.exe" install -r "%ROOT%requirements.txt" pyinstaller -q
)
"%PY%" "%ROOT%build.py"
echo.
echo Готово: dist\UnblockHelper\UnblockHelper.exe
pause
exit /b 0

:cli
if not exist "%PY%" (
  py -3 -m venv "%ROOT%.venv"
  "%ROOT%.venv\Scripts\pip.exe" install -r "%ROOT%requirements.txt" -q
)
shift
"%PY%" "%ROOT%main.py" %*
exit /b %ERRORLEVEL%

:kill
echo Завершение зависших процессов...
taskkill /IM UnblockHelper.exe /F >nul 2>&1
for /f "tokens=2" %%P in ('tasklist /FI "IMAGENAME eq pythonw.exe" /FO LIST 2^>nul ^| findstr /I "PID:"') do (
  wmic process where "ProcessId=%%P" get CommandLine 2^>nul | findstr /I "desktop.app" >nul && taskkill /PID %%P /F >nul 2>&1
)
del "%TEMP%\unblock-helper-desktop.pid" >nul 2>&1
echo Готово.
pause
exit /b 0

:run
if exist "%EXE%" (
  call :elevate "%EXE%" "%WORKDIR%"
  exit /b 0
)

if not exist "%PY%" (
  echo Создание окружения...
  py -3 -m venv "%ROOT%.venv"
  "%ROOT%.venv\Scripts\pip.exe" install -r "%ROOT%requirements.txt" -q
)

call :elevate "%PY%" "%ROOT%"
exit /b 0

:elevate
set "CMD=%~1"
set "WD=%~2"
net session >nul 2>&1
if %errorlevel% equ 0 goto launch
echo Запрос прав администратора (UAC)...
if "%CMD:~-3%"=="exe" (
  powershell -NoProfile -Command "Start-Process -FilePath '%CMD%' -Verb RunAs -WorkingDirectory '%WD%'"
) else (
  powershell -NoProfile -Command "Start-Process -FilePath '%CMD%' -ArgumentList '%APP%' -Verb RunAs -WorkingDirectory '%WD%'"
)
exit /b 0

:launch
if "%CMD:~-3%"=="exe" (
  start "" /D "%WD%" "%CMD%"
) else (
  start "" /D "%WD%" "%CMD%" "%APP%"
)
exit /b 0
