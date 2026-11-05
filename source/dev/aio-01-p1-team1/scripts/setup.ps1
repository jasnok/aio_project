param([ValidateSet('All', 'BE', 'FE_Admin', 'FE_User')][string]$App = 'All')
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$apps = if ($App -eq 'All') { @('BE', 'FE_Admin', 'FE_User') } else { @($App) }
Push-Location $repoRoot
try {
    foreach ($name in $apps) {
        $pythonPath = Join-Path $repoRoot "$name/.venv/Scripts/python.exe"
        if (-not (Test-Path -LiteralPath $pythonPath)) {
            python -m venv "$name/.venv"
            if ($LASTEXITCODE -ne 0) { throw "Could not create $name environment. Install Python 3.11+." }
        }
        & $pythonPath -m pip install -r "$name/requirements.txt"
        if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed: $name" }
    }
} finally { Pop-Location }
