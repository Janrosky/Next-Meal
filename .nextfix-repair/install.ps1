$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$logDirectory = Join-Path $projectRoot 'logs'
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
$transcribing = $false
$result = 1
try {
    Start-Transcript -Path (Join-Path $logDirectory 'install.log') -Force | Out-Null
    $transcribing = $true
    Write-Host '[1/4] Comprobando Python y Node.js...'
    $node = Get-Command node.exe -ErrorAction SilentlyContinue
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $node -or -not $npm) { throw 'Instala Node.js 22 o superior y vuelve a ejecutar Instalar.cmd.' }
    $nodeVersion = & $node.Source --version
    if ($LASTEXITCODE -ne 0 -or [int]($nodeVersion.TrimStart('v').Split('.')[0]) -lt 22) { throw 'Se necesita Node.js 22 o superior.' }

    $venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $venvPython)) {
        $candidates = @(
            @{ Command = 'py.exe'; Prefix = @('-3') },
            @{ Command = 'python.exe'; Prefix = @() }
        )
        $pythonCommand = $null
        $pythonPrefix = @()
        foreach ($candidate in $candidates) {
            $resolved = Get-Command $candidate.Command -ErrorAction SilentlyContinue
            if (-not $resolved) { continue }
            $prefix = $candidate.Prefix
            & $resolved.Source @prefix -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'
            if ($LASTEXITCODE -eq 0) {
                $pythonCommand = $resolved.Source
                $pythonPrefix = $prefix
                break
            }
        }
        if (-not $pythonCommand) { throw 'Instala Python 3.12 o superior (3.14 tambien es compatible).' }
        & $pythonCommand @pythonPrefix -m venv (Join-Path $projectRoot '.venv')
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno de Python.' }
    }
    & $venvPython -c 'import sys; print(sys.version); sys.exit(0 if sys.version_info >= (3, 12) else 1)'
    if ($LASTEXITCODE -ne 0) { throw 'El entorno .venv no contiene un Python compatible. No se modificaron tus datos.' }

    Write-Host '[2/4] Instalando el servidor...'
    & $venvPython -m pip install -e (Join-Path $projectRoot 'backend')
    if ($LASTEXITCODE -ne 0) { throw 'Fallo la instalacion del servidor. Comprueba la conexion a internet y vuelve a intentar.' }
    & $venvPython -c 'import fastapi, uvicorn, sqlalchemy; from app.main import create_app'
    if ($LASTEXITCODE -ne 0) { throw 'Las dependencias del servidor no se instalaron correctamente.' }

    Write-Host '[3/4] Instalando y compilando la interfaz...'
    Push-Location (Join-Path $projectRoot 'frontend')
    try {
        & $npm.Source ci
        if ($LASTEXITCODE -ne 0) { throw 'Fallo la instalacion de la interfaz. Comprueba la conexion a internet.' }
        & $npm.Source run build
        if ($LASTEXITCODE -ne 0) { throw 'Fallo la compilacion de la interfaz.' }
    } finally { Pop-Location }
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend\dist\index.html'))) {
        throw 'No se genero la interfaz de Next-Fix.'
    }
    Write-Host '[4/4] Instalacion verificada.'
    Write-Host 'Listo. Ejecuta Iniciar.cmd. Next-Fix usara http://127.0.0.1:8001'
    $result = 0
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host ('Detalle: ' + (Join-Path $logDirectory 'install.log'))
} finally {
    if ($transcribing) { Stop-Transcript | Out-Null }
}
exit $result
