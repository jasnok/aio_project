param([string]$HostIp = "192.100.200.232")

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$rootPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$python = if (Test-Path -LiteralPath $rootPython) { $rootPython } else { "python" }

Write-Host "[1/7] pgvector DB"
$health = docker inspect --format '{{.State.Health.Status}}' mcp-2team-pgvector
if ($health -ne "healthy") { throw "DB 상태가 healthy가 아닙니다: $health" }
docker exec mcp-2team-pgvector psql -U mcp_user -d travel_mcp -v ON_ERROR_STOP=1 `
    -c "SELECT extversion AS vector_version FROM pg_extension WHERE extname='vector';" `
    -c "SELECT (SELECT COUNT(*) FROM hotels) AS hotels, (SELECT COUNT(*) FROM tourist_attractions) AS attractions, (SELECT COUNT(*) FROM hotel_policies) AS policies, (SELECT COUNT(*) FROM tour_documents) AS documents;"

Write-Host "[2/7] Ollama embedding"
$ollamaHealth = docker inspect --format '{{.State.Health.Status}}' mcp-2team-ollama
if ($ollamaHealth -ne "healthy") { throw "Ollama 상태가 healthy가 아닙니다." }
$ollamaTags = Invoke-RestMethod -Uri "http://127.0.0.1:11435/api/tags" -TimeoutSec 20
$modelNames = @($ollamaTags.models | ForEach-Object { $_.name })
if (-not ($modelNames | Where-Object { $_ -like "embeddinggemma:*" })) {
    throw "embeddinggemma 모델이 없습니다."
}

Write-Host "[3/7] Tour/Weather MCP Tool discovery"
Push-Location $projectRoot
try {
    & $python run\check_mcp_http.py
    if ($LASTEXITCODE -ne 0) { throw "MCP Tool discovery 실패" }
}
finally {
    Pop-Location
}

Write-Host "[4/7] 부산 호텔 → 정책 RAG 시나리오"
Push-Location $projectRoot
try {
    & $python run\check_tour_scenario.py
    if ($LASTEXITCODE -ne 0) { throw "Tour 시나리오 점검 실패" }
}
finally {
    Pop-Location
}

Write-Host "[5/7] Backend health"
$healthResponse = Invoke-RestMethod -Uri "http://${HostIp}:8000/health" -TimeoutSec 20
if ($healthResponse.status -ne "ok") { throw "Backend health 실패" }

Write-Host "[6/7] Backend → MCP 연결"
$mcpStatus = Invoke-RestMethod -Uri "http://${HostIp}:8000/api/mcp/status" -TimeoutSec 30
if ($mcpStatus.status -ne "connected") { throw "MCP 연결이 완전하지 않습니다." }
$mcpStatus.servers | Select-Object name, status, transport, endpoint, tool_count | Format-Table

Write-Host "[7/7] Frontend HTTP"
$frontend = Invoke-WebRequest -Uri "http://${HostIp}:8501" -UseBasicParsing -TimeoutSec 20
if ($frontend.StatusCode -ne 200) { throw "Frontend HTTP 확인 실패" }

Write-Host "전체 로컬 인프라 검사가 통과했습니다."
