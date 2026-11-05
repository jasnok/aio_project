$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$statePath = Join-Path $PSScriptRoot ".local-processes.json"
$composeFile = Join-Path $projectRoot "resources\database\docker-compose.yml"
$databaseEnv = Join-Path $projectRoot "resources\database\.env"

if (Test-Path -LiteralPath $statePath) {
    $processes = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    foreach ($property in $processes.PSObject.Properties) {
        $processId = [int]$property.Value
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        Write-Host "$($property.Name) 종료 요청: PID $processId"
    }
    Remove-Item -LiteralPath $statePath -Force
}
else {
    Write-Host "저장된 로컬 프로세스가 없습니다."
}

docker compose --env-file $databaseEnv -f $composeFile stop
Write-Host "pgvector 컨테이너를 중지했습니다. DB volume은 보존됩니다."
