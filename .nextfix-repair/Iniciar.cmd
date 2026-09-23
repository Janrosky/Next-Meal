@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Falta el entorno de Python. Ejecuta Instalar.cmd y comprueba que termine correctamente.
  if /i not "%~1"=="--no-pause" pause
  exit /b 1
)
cd backend
"..\.venv\Scripts\python.exe" -m app.launcher
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" if /i not "%~1"=="--no-pause" pause
exit /b %RESULT%
