param(
    [Parameter(Mandatory = $true)][ValidateSet('BE', 'FE_Admin', 'FE_User')][string]$App,
    [ValidateRange(1, 65535)][int]$Port
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoRoot "$App/.venv/Scripts/python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run scripts/setup.ps1 first.' }
if (-not $Port) { $Port = @{ BE = 8000; FE_User = 8501; FE_Admin = 8502 }[$App] }
Push-Location (Join-Path $repoRoot $App)
try {
    if ($App -eq 'BE') {
        & $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port $Port
    } else {
        & $pythonPath -m streamlit run app.py --server.address 127.0.0.1 --server.port $Port --server.headless true
    }
    if ($LASTEXITCODE -ne 0) { throw "App failed to start: $App" }
} finally { Pop-Location }
