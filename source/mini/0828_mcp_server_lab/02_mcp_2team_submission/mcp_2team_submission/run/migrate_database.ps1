$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$compose = Join-Path $projectRoot "resources\database\docker-compose.yml"
$databaseEnv = Join-Path $projectRoot "resources\database\.env"

docker compose --env-file $databaseEnv -f $compose up -d pgvector
$deadline = (Get-Date).AddSeconds(90)
do {
    $health = docker inspect --format '{{.State.Health.Status}}' mcp-2team-pgvector 2>$null
    if ($health -eq "healthy") { break }
    Start-Sleep -Seconds 2
} while ((Get-Date) -lt $deadline)
if ($health -ne "healthy") { throw "pgvector DB가 healthy 상태가 되지 않았습니다." }

docker exec mcp-2team-pgvector psql -U mcp_user -d travel_mcp -v ON_ERROR_STOP=1 `
    -f /docker-entrypoint-initdb.d/migrations/004_multi_embedding_provider.sql
if ($LASTEXITCODE -ne 0) { throw "다중 임베딩 Migration 실패" }
docker exec mcp-2team-pgvector psql -U mcp_user -d travel_mcp -v ON_ERROR_STOP=1 `
    -f /docker-entrypoint-initdb.d/migrations/005_hotel_policies.sql
if ($LASTEXITCODE -ne 0) { throw "호텔 정책 Migration 실패" }

docker exec mcp-2team-pgvector psql -U mcp_user -d travel_mcp -v ON_ERROR_STOP=1 `
    -c "SELECT COUNT(*) AS policies FROM hotel_policies;"
Write-Host "DB Migration 완료"
