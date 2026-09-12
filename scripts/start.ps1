param([int]$Port = 8000, [string]$BindAddress = '0.0.0.0')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { throw 'Ejecutá Instalar.cmd primero.' }
if (-not (Test-Path -LiteralPath 'frontend\dist\index.html')) { throw 'Ejecutá Instalar.cmd para compilar la interfaz.' }
& .\.venv\Scripts\python.exe -m app.cli init --demo
if ($LASTEXITCODE -ne 0) { throw 'No se pudo completar la configuración inicial.' }
Write-Host ''
Write-Host "Autoservicio: http://localhost:$Port"
Write-Host "Empleados:    http://localhost:$Port/#/staff"
Write-Host 'Desde otros equipos: usá la IP de esta computadora y el mismo puerto.'
Write-Host 'Mantené esta ventana abierta. Para detener el servidor: Ctrl+C.'
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host $BindAddress --port $Port --workers 1

