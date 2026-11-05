param([ValidateSet('Start', 'Stop', 'Status')][string]$Action = 'Status')
$ErrorActionPreference = 'Stop'

$containerName = 'housing-portfolio-local-redis'
$projectLabel = 'aio-01-p1-team1'
$port = 16379

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker is required for local Redis. Start Docker Desktop first.'
}

$ErrorActionPreference = 'Continue'
$containerJson = docker inspect $containerName 2>$null
$inspectExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
$container = if ($inspectExit -eq 0) { ($containerJson | ConvertFrom-Json)[0] } else { $null }

if ($container -and $container.Config.Labels.'aio.project' -ne $projectLabel) {
    throw "Container name $containerName is already used by another project."
}

switch ($Action) {
    'Start' {
        if ($container) {
            if (-not $container.State.Running) { docker start $containerName | Out-Null }
        } else {
            if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
                throw "Port $port is already in use."
            }
            docker run -d --name $containerName --label "aio.project=$projectLabel" `
                --publish "127.0.0.1:${port}:6379" redis:7 | Out-Null
        }
        if ($LASTEXITCODE -ne 0) { throw 'Local Redis failed to start.' }
        $reply = docker exec $containerName redis-cli ping
        if ($LASTEXITCODE -ne 0 -or $reply -ne 'PONG') { throw 'Local Redis did not answer PING.' }
        Write-Output "Local Redis ready at 127.0.0.1:$port."
    }
    'Stop' {
        if ($container -and $container.State.Running) {
            docker stop $containerName | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'Local Redis failed to stop.' }
        }
        Write-Output 'Local Redis stopped.'
    }
    'Status' {
        if ($container -and $container.State.Running) {
            $reply = docker exec $containerName redis-cli ping
            if ($LASTEXITCODE -ne 0 -or $reply -ne 'PONG') { throw 'Local Redis is running but not healthy.' }
            Write-Output "Local Redis ready at 127.0.0.1:$port."
        } else {
            Write-Output 'Local Redis is stopped.'
        }
    }
}
