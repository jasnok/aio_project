param([ValidateSet('Start', 'Stop', 'Status')][string]$Action = 'Status')
$ErrorActionPreference = 'Stop'
Import-Module Microsoft.PowerShell.Utility
$repoRoot = Split-Path -Parent $PSScriptRoot
$localCli = Join-Path $repoRoot '.runtime/tools/supabase.exe'
$manifest = Join-Path $repoRoot '.runtime/tools/supabase-provenance.json'
if ((Test-Path -LiteralPath $localCli) -and (Test-Path -LiteralPath $manifest)) {
    $expected = (Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json).binary_sha256
    $actual = (Get-FileHash -LiteralPath $localCli -Algorithm SHA256).Hash
    if ($actual -ne $expected) { throw 'Local Supabase CLI SHA-256 mismatch.' }
    $cli = $localCli
} elseif (Get-Command supabase -ErrorAction SilentlyContinue) {
    $cli = (Get-Command supabase).Source
} else {
    throw 'Supabase CLI is not installed. See docs/database_step3.md. No cloud settings were changed.'
}
Push-Location $repoRoot
try {
    switch ($Action) {
        'Start' { & $cli start --exclude studio,postgres-meta,edge-runtime,logflare,vector,supavisor,imgproxy,realtime,mailpit }
        'Stop' { & $cli stop }
        'Status' { & $cli status }
    }
    if ($LASTEXITCODE -ne 0) { throw "Local database command failed: $Action" }
} finally { Pop-Location }
