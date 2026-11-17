param([string]$Model = "embeddinggemma")

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$compose = Join-Path $projectRoot "resources\database\docker-compose.yml"
$databaseEnv = Join-Path $projectRoot "resources\database\.env"
$portLine = Get-Content -LiteralPath $databaseEnv | Where-Object { $_ -match '^OLLAMA_PORT=' } | Select-Object -First 1
$ollamaPort = if ($portLine) { ($portLine -split '=', 2)[1] } else { "11435" }

docker compose --env-file $databaseEnv -f $compose up -d ollama
$deadline = (Get-Date).AddSeconds(120)
do {
    $health = docker inspect --format '{{.State.Health.Status}}' mcp-2team-ollama 2>$null
    if ($health -eq "healthy") { break }
    Start-Sleep -Seconds 2
} while ((Get-Date) -lt $deadline)
if ($health -ne "healthy") { throw "Ollama 컨테이너가 healthy 상태가 되지 않았습니다." }

docker exec mcp-2team-ollama ollama pull $Model
if ($LASTEXITCODE -ne 0) { throw "Ollama 모델 다운로드 실패: $Model" }

$payload = @{ model = $Model; input = "부산 호텔 당일 취소 규정" } | ConvertTo-Json
$result = Invoke-RestMethod -Uri "http://127.0.0.1:${ollamaPort}/api/embed" `
    -Method Post -ContentType "application/json; charset=utf-8" -Body $payload -TimeoutSec 180
$dimension = $result.embeddings[0].Count
if ($dimension -lt 1) { throw "Ollama 임베딩 벡터가 비어 있습니다." }
Write-Host "Ollama 준비 완료: model=$Model, dimension=$dimension"
