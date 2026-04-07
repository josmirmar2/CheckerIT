param(
  [switch]$BackendOnly,
  [switch]$FrontendOnly,
  [switch]$SkipInstall,
  [ValidateSet('windows', 'background')]
  [string]$Mode = 'windows',
  [switch]$OpenBrowser
)

$ErrorActionPreference = 'Stop'

function Assert-Path($path, $message) {
  if (-not (Test-Path $path)) {
    throw $message
  }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$backendDir = Join-Path $repoRoot 'backend'
$frontendDir = Join-Path $repoRoot 'frontend'

Assert-Path (Join-Path $backendDir 'manage.py') "No encuentro backend/manage.py. Ejecuta este script desde la carpeta del proyecto (o no muevas scripts/dev.ps1)."
Assert-Path (Join-Path $frontendDir 'package.json') "No encuentro frontend/package.json. Ejecuta este script desde la carpeta del proyecto (o no muevas scripts/dev.ps1)."

$runBackend = -not $FrontendOnly
$runFrontend = -not $BackendOnly

if ($BackendOnly -and $FrontendOnly) {
  throw 'No uses -BackendOnly y -FrontendOnly a la vez.'
}

if ($runBackend) {
  Write-Host "[Backend] Preparando entorno..." -ForegroundColor Cyan

  # VENV: versiones antiguas usaban backend/venv. Actualmente preferimos .venv en la raíz.
  $venvCandidates = @(
    (Join-Path $repoRoot '.venv\Scripts\python.exe'),
    (Join-Path $backendDir '.venv\Scripts\python.exe'),
    (Join-Path $backendDir 'venv\Scripts\python.exe')
  )

  $venvPython = $venvCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

  if (-not $venvPython) {
    $venvDir = Join-Path $repoRoot '.venv'
    Write-Host "[Backend] Creando venv en $venvDir ..." -ForegroundColor Cyan
    Push-Location $repoRoot
    try {
      python -m venv .venv
    } finally {
      Pop-Location
    }
    $venvPython = Join-Path $venvDir 'Scripts\python.exe'
  }

  if (-not (Test-Path $venvPython)) {
    throw "No se pudo localizar/crear el venv. Comprueba que 'python' está en PATH y que tienes permisos."
  }

  if (-not $SkipInstall) {
    Write-Host "[Backend] Instalando dependencias..." -ForegroundColor Cyan
    Push-Location $backendDir
    try {
      & $venvPython -m pip install --upgrade pip
      & $venvPython -m pip install -r requirements.txt
    } finally {
      Pop-Location
    }
  } else {
    Write-Host "[Backend] SkipInstall activado: no instalo dependencias." -ForegroundColor Yellow
  }

  if (-not (Test-Path (Join-Path $backendDir '.env'))) {
    Write-Host "[Backend] Aviso: no existe backend/.env. Se usarán valores por defecto o variables de entorno." -ForegroundColor Yellow
  }

  Write-Host "[Backend] Ejecutando migraciones..." -ForegroundColor Cyan
  Push-Location $backendDir
  try {
    $env:PGCLIENTENCODING = 'UTF8'
    & $venvPython manage.py migrate
  } finally {
    Pop-Location
  }

  Write-Host "[Backend] Arrancando servidor (http://localhost:8000)..." -ForegroundColor Green

  if ($Mode -eq 'windows') {
    $backendCmd = "& '$venvPython' manage.py runserver"
    Start-Process -FilePath 'powershell' -WorkingDirectory $backendDir -ArgumentList @('-NoProfile', '-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', $backendCmd)
  } else {
    Start-Process -FilePath $venvPython -ArgumentList 'manage.py','runserver' -WorkingDirectory $backendDir
  }
}

if ($runFrontend) {
  Write-Host "[Frontend] Preparando frontend..." -ForegroundColor Cyan

  if (-not $SkipInstall) {
    Write-Host "[Frontend] npm install..." -ForegroundColor Cyan
    Push-Location $frontendDir
    try {
      npm install
    } finally {
      Pop-Location
    }
  } else {
    Write-Host "[Frontend] SkipInstall activado: no ejecuto npm install." -ForegroundColor Yellow
  }

  if (-not (Test-Path (Join-Path $frontendDir '.env'))) {
    Write-Host "[Frontend] Aviso: no existe frontend/.env. Revisa REACT_APP_API_URL si lo necesitas." -ForegroundColor Yellow
  }

  Write-Host "[Frontend] Arrancando servidor (http://localhost:3000)..." -ForegroundColor Green

  if ($Mode -eq 'windows') {
    Start-Process -FilePath 'powershell' -WorkingDirectory $frontendDir -ArgumentList @('-NoProfile', '-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', 'npm start')
  } else {
    Start-Process -FilePath 'npm' -ArgumentList 'start' -WorkingDirectory $frontendDir
  }
}

if ($OpenBrowser) {
  Start-Sleep -Seconds 2
  if ($runFrontend) {
    Start-Process 'http://localhost:3000'
  } elseif ($runBackend) {
    Start-Process 'http://localhost:8000'
  }
}

if ($Mode -eq 'windows') {
  Write-Host "Listo. Se han abierto ventanas con los logs. Para parar: cierra esas ventanas o usa Ctrl+C en cada una." -ForegroundColor Green
} else {
  Write-Host "Listo. Los servidores se han lanzado en segundo plano." -ForegroundColor Green
  Write-Host "Abre manualmente: http://localhost:3000 (frontend) y http://localhost:8000 (backend)." -ForegroundColor Green
}