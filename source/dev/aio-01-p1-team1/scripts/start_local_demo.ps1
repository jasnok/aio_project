param(
    [Parameter(Mandatory = $true)][ValidateSet('BE', 'FE_User', 'FE_Admin')][string]$App,
    [ValidateRange(1, 65535)][int]$Port,
    [ValidateRange(1, 65535)][int]$BackendPort = 8000
)
$ErrorActionPreference = 'Stop'
Import-Module Microsoft.PowerShell.Utility
$repoRoot = Split-Path -Parent $PSScriptRoot
$localCli = Join-Path $repoRoot '.runtime/tools/supabase.exe'
$manifest = Join-Path $repoRoot '.runtime/tools/supabase-provenance.json'
if ((Test-Path -LiteralPath $localCli) -and (Test-Path -LiteralPath $manifest)) {
    $expected = (Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json).binary_sha256
    if ((Get-FileHash -LiteralPath $localCli -Algorithm SHA256).Hash -ne $expected) {
        throw 'Local Supabase CLI SHA-256 mismatch.'
    }
    $cli = $localCli
} elseif (Get-Command supabase -ErrorAction SilentlyContinue) {
    $cli = (Get-Command supabase).Source
} else {
    throw 'Supabase CLI is not installed. See docs/database_step3.md.'
}

Push-Location $repoRoot
try {
    # Supabase CLI의 정상 상태 안내도 stderr로 출력됩니다. JSON만 처리합니다.
    $ErrorActionPreference = 'Continue'
    $statusJson = & $cli status -o json 2>$null
    $cliExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($cliExit -ne 0) {
        throw 'Local Supabase is not running. Run scripts/local_db.ps1 -Action Start first.'
    }
    $status = $statusJson | ConvertFrom-Json
    if (-not $status.API_URL) { throw 'Local Supabase status did not include an API URL.' }
    $env:SUPABASE_URL = $status.API_URL
    if ($App -eq 'BE') {
        $env:SUPABASE_SERVICE_ROLE_KEY = $status.SERVICE_ROLE_KEY
        # 파일을 다시 실행해도 같은 키를 사용합니다. 실제 키는 Git에 올리지 않습니다.
        $secretPath = Join-Path $repoRoot '.runtime/admin-token-secret'
        if (-not (Test-Path -LiteralPath $secretPath)) {
            New-Item -ItemType Directory -Path (Split-Path -Parent $secretPath) -Force | Out-Null
            $bytes = New-Object byte[] 48
            $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
            try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
            [Convert]::ToBase64String($bytes) | Set-Content -LiteralPath $secretPath -Encoding ascii -NoNewline
        }
        $env:ADMIN_TOKEN_SECRET = (Get-Content -LiteralPath $secretPath -Raw).Trim()
        if ($env:ADMIN_TOKEN_SECRET.Length -lt 32) { throw 'Local admin token secret is too short.' }
        # 로컬 시연에서는 유료 AI 요청을 막고 이 프로젝트 전용 Redis를 사용합니다.
        $env:CHAT_GEMINI_MODE = 'mock'
        $env:REDIS_URL = 'redis://127.0.0.1:16379/0'
    } elseif ($App -eq 'FE_User') {
        $env:SUPABASE_ANON_KEY = $status.ANON_KEY
    }
    $env:BACKEND_URL = "http://127.0.0.1:$BackendPort"
    Write-Output "Starting $App against local Supabase at $($status.API_URL). Keys are hidden."
    if ($Port) {
        & (Join-Path $repoRoot 'scripts/start.ps1') -App $App -Port $Port
    } else {
        & (Join-Path $repoRoot 'scripts/start.ps1') -App $App
    }
    if ($LASTEXITCODE -ne 0) { throw "$App stopped with an error." }
} finally {
    Pop-Location
}
