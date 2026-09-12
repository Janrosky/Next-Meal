$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Instalá Python 3.12 o superior y agregalo al PATH.' }
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw 'Instalá Node.js 22 o superior.' }
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno de Python.' }
}
& .\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
& .\.venv\Scripts\python.exe -m pip install --no-deps -e ./backend
if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar el servidor.' }
Push-Location frontend
try {
    & npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias de la interfaz.' }
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar la interfaz.' }
} finally { Pop-Location }
Write-Host 'Instalación lista. Ejecutá Iniciar.cmd.'

