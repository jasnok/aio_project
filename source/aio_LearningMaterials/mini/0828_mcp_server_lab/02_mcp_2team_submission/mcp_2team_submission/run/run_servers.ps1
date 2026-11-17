$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$rootPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$tourPython = Join-Path $projectRoot "app\tour\.venv\Scripts\python.exe"
$weatherPython = Join-Path $projectRoot "app\weather\.venv\Scripts\python.exe"

if (Test-Path -LiteralPath $rootPython) {
    $tourPython = $rootPython
    $weatherPython = $rootPython
}
elseif (-not (Test-Path -LiteralPath $tourPython) -or -not (Test-Path -LiteralPath $weatherPython)) {
    throw "루트 .venv 또는 서버별 .venv가 없습니다. README의 설치 절차를 먼저 실행해 주세요."
}

Push-Location $projectRoot
try {
    Write-Host "Tour MCP(8020)와 Weather MCP(8013)를 실행합니다. 종료: Ctrl+C"
    $tourJob = Start-Job -Name "tour-mcp" -ScriptBlock {
        param($pythonPath, $workingDirectory)
        Set-Location $workingDirectory
        & $pythonPath -m app.tour.main
    } -ArgumentList $tourPython, $projectRoot
    $weatherJob = Start-Job -Name "weather-mcp" -ScriptBlock {
        param($pythonPath, $workingDirectory)
        Set-Location $workingDirectory
        & $pythonPath -m app.weather.main
    } -ArgumentList $weatherPython, $projectRoot

    Receive-Job -Job $tourJob, $weatherJob -Wait
}
finally {
    Get-Job -Name "tour-mcp", "weather-mcp" -ErrorAction SilentlyContinue |
        Stop-Job -ErrorAction SilentlyContinue
    Get-Job -Name "tour-mcp", "weather-mcp" -ErrorAction SilentlyContinue |
        Remove-Job -Force -ErrorAction SilentlyContinue
    Pop-Location
}
