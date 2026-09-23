@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install.ps1"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" echo La instalacion fallo. Revisa el mensaje anterior y logs\install.log.
if /i not "%~1"=="--no-pause" pause
exit /b %RESULT%
