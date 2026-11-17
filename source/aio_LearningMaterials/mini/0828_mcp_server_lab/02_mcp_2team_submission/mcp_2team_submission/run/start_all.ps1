param(
    [string]$PythonCommand = "python"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$rootPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$python = if (Test-Path -LiteralPath $rootPython) { $rootPython } else { $PythonCommand }
$logsDir = Join-Path $projectRoot "logs"
$statePath = Join-Path $PSScriptRoot ".local-processes.json"
$composeFile = Join-Path $projectRoot "resources\database\docker-compose.yml"
$databaseEnv = Join-Path $projectRoot "resources\database\.env"

New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

function Wait-Http([string]$Name, [string]$Url, [int]$TimeoutSeconds = 60) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Host "$Name 준비 완료: $Url"
                return
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    } while ((Get-Date) -lt $deadline)
    throw "$Name 시작 제한 시간을 초과했습니다: $Url"
}

function Wait-Tcp([string]$Name, [int]$Port, [int]$TimeoutSeconds = 60) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        if (Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -InformationLevel Quiet) {
            Write-Host "$Name 준비 완료: port $Port"
            return
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "$Name 시작 제한 시간을 초과했습니다: port $Port"
}

function Start-LocalProcess(
    [string]$Name,
    [string[]]$Arguments
) {
    $outLog = Join-Path $logsDir "$Name.out.log"
    $errorLog = Join-Path $logsDir "$Name.error.log"
    $process = Start-Process -FilePath $python `
        -ArgumentList $Arguments `
        -WorkingDirectory $projectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $outLog `
        -RedirectStandardError $errorLog `
        -PassThru
    Write-Host "$Name 시작: PID $($process.Id)"
    return $process.Id
}

if (Test-Path -LiteralPath $statePath) {
    throw "기존 실행 상태 파일이 있습니다. 먼저 .\run\stop_all.ps1을 실행해 주세요."
}

Push-Location $projectRoot
try {
    docker info --format '{{.ServerVersion}}' | Out-Null
    docker compose --env-file $databaseEnv -f $composeFile up -d

    $deadline = (Get-Date).AddSeconds(90)
    do {
        $dbHealth = docker inspect --format '{{.State.Health.Status}}' mcp-2team-pgvector 2>$null
        if ($dbHealth -eq "healthy") { break }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    if ($dbHealth -ne "healthy") { throw "pgvector DB가 healthy 상태가 되지 않았습니다." }

    $deadline = (Get-Date).AddSeconds(120)
    do {
        $ollamaHealth = docker inspect --format '{{.State.Health.Status}}' mcp-2team-ollama 2>$null
        if ($ollamaHealth -eq "healthy") { break }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    if ($ollamaHealth -ne "healthy") { throw "Ollama가 healthy 상태가 되지 않았습니다." }

    $processes = [ordered]@{}
    $processes.tour = Start-LocalProcess "tour-mcp" @("-m", "app.tour.main")
    $processes.weather = Start-LocalProcess "weather-mcp" @("-m", "app.weather.main")
    Wait-Tcp "Tour MCP" 8020
    Wait-Tcp "Weather MCP" 8013

    $processes.backend = Start-LocalProcess "backend" @(
        "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"
    )
    Wait-Http "Backend" "http://127.0.0.1:8000/health"

    $processes.frontend = Start-LocalProcess "frontend" @(
        "-m", "streamlit", "run", "frontend\app.py",
        "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true"
    )
    Wait-Http "Frontend" "http://127.0.0.1:8501"

    $processes | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
    Write-Host "전체 서버가 실행됐습니다. 상태 확인: .\run\check_all.ps1"
}
catch {
    if ($processes) {
        foreach ($processId in $processes.Values) {
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
    throw
}
finally {
    Pop-Location
}
