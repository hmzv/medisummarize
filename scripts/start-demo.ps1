param([int]$ApiPort = 8000, [int]$WebPort = 5173)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendPython = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'
$frontendRoot = Join-Path $projectRoot 'frontend'
$viteEntry = Join-Path $frontendRoot 'node_modules\vite\bin\vite.js'
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot '.env'))) { throw 'Create .env from .env.example and configure SECRET_KEY and DATABASE_URL first.' }
if (-not (Test-Path -LiteralPath $backendPython)) { throw 'Install the backend virtual environment using README.md first.' }
if (-not (Test-Path -LiteralPath $viteEntry)) { throw 'Run npm install in frontend first.' }
if ($ApiPort -ne 8000) { throw 'The Vite proxy currently targets port 8000. Keep ApiPort=8000 or edit vite.config.ts first.' }
$nodeCommand = (Get-Command node -ErrorAction Stop).Source
$logDirectory = Join-Path $projectRoot 'data\runtime\demo-logs'
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
if (-not (Get-NetTCPConnection -State Listen -LocalPort $ApiPort -ErrorAction SilentlyContinue)) {
    Push-Location (Join-Path $projectRoot 'backend')
    try { & $backendPython -m alembic upgrade head; if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' } }
    finally { Pop-Location }
    Start-Process -FilePath $backendPython -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port',"$ApiPort" -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDirectory 'api.log') -RedirectStandardError (Join-Path $logDirectory 'api-error.log') | Out-Null
} else { Write-Host "Port $ApiPort is already listening. Check the health link below to confirm the expected API." }
if (-not (Get-NetTCPConnection -State Listen -LocalPort $WebPort -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $nodeCommand -ArgumentList ('"' + $viteEntry + '"'),'--host','127.0.0.1','--port',"$WebPort",'--strictPort' -WorkingDirectory $frontendRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDirectory 'web.log') -RedirectStandardError (Join-Path $logDirectory 'web-error.log') | Out-Null
}
Write-Host "Frontend: http://localhost:$WebPort"
Write-Host "API health: http://127.0.0.1:$ApiPort/api/v1/health"
Write-Host "Logs: $logDirectory"
Write-Host 'Generation remains configured by your .env. Mock output is not a model-quality result.'
