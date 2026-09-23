@echo off
cd /d "%~dp0"
echo [1/4] Preparando Python...
if not exist ".venv\Scripts\python.exe" py -3.12 -m venv .venv
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -e "./backend"
echo [2/4] Preparando interfaz...
cd frontend
call npm install
call npm run build
cd ..
echo [3/4] Creando datos locales...
if not exist "data" mkdir data
echo [4/4] Listo.
echo Ejecuta Iniciar.cmd para abrir Next-Fix.
pause
