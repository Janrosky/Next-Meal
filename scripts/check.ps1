$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
& .\.venv\Scripts\python.exe -m ruff check backend
if ($LASTEXITCODE -ne 0) { throw 'Falló la revisión de estilo.' }
& .\.venv\Scripts\python.exe -m ruff format --check backend
if ($LASTEXITCODE -ne 0) { throw 'Hay archivos sin formatear.' }
Push-Location backend
try {
    & ..\.venv\Scripts\python.exe -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Fallaron las pruebas del servidor.' }
} finally { Pop-Location }
Push-Location frontend
try {
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación.' }
    & npm.cmd run test:e2e
    if ($LASTEXITCODE -ne 0) { throw 'Fallaron las pruebas del navegador.' }
} finally { Pop-Location }

