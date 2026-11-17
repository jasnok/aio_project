param(
    [switch]$Integration
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$rootPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$python = if (Test-Path -LiteralPath $rootPython) { $rootPython } else { "python" }

Push-Location $projectRoot
try {
    Write-Host "[1/2] Python 문법을 검사합니다."
    & $python -m compileall -q app backend frontend resources\database run
    if ($LASTEXITCODE -ne 0) { throw "Python 문법 검사에 실패했습니다." }

    Write-Host "[2/2] Tour 단위 테스트를 실행합니다."
    & $python -m unittest discover -s app\tour\tests -p "test_*.py" -v
    if ($LASTEXITCODE -ne 0) { throw "Tour 단위 테스트에 실패했습니다." }

    Write-Host "Weather 단위 테스트를 실행합니다."
    & $python -m unittest discover -s app\weather\tests -p "test_*.py" -v
    if ($LASTEXITCODE -ne 0) { throw "Weather 단위 테스트에 실패했습니다." }

    if ($Integration) {
        Write-Host "실행 중인 두 MCP 서버의 Tool 목록을 확인합니다."
        & $python run\check_mcp_http.py
        if ($LASTEXITCODE -ne 0) { throw "MCP HTTP 통합 점검에 실패했습니다." }
    }

    Write-Host "모든 검사가 통과했습니다."
}
finally {
    Pop-Location
}
