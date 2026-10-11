# Abre o Airflow no navegador. Se ele estiver parado, abre o Docker Desktop e sobe os containers antes.
#
#   -PastaWsl   pasta do lab-dados dentro do Ubuntu (WSL), de onde os containers sobem
#   -NoOpen     faz tudo menos abrir o navegador (usado para testar)
param(
    [string]$PastaWsl = '~/projetos/lab-dados',
    [switch]$NoOpen
)

$url = 'http://localhost:8080'
$docker = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe'

function Test-Airflow {
    try { return (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200 } catch { return $false }
}

function Test-Docker {
    docker info *> $null
    return ($LASTEXITCODE -eq 0)
}

function Fail($msg) {
    Write-Host ""
    Write-Host $msg -ForegroundColor Red
    Read-Host "Aperte Enter para fechar"
    exit 1
}

if (-not (Test-Airflow)) {
    Write-Host "Airflow parado. Iniciando..." -ForegroundColor Yellow

    if (-not (Test-Docker)) {
        Write-Host "Abrindo o Docker Desktop (pode levar 1 a 2 minutos)..."
        if (-not (Test-Path $docker)) { Fail "Docker Desktop nao encontrado em: $docker" }
        Start-Process $docker
        $limite = (Get-Date).AddSeconds(240)
        while (-not (Test-Docker)) {
            if ((Get-Date) -gt $limite) { Fail "O Docker nao ficou pronto a tempo. Abra o Docker Desktop e tente de novo." }
            Start-Sleep -Seconds 5
        }
    }

    Write-Host "Subindo PostgreSQL, n8n e Airflow..."
    wsl -d Ubuntu -- bash -c "cd $PastaWsl && docker compose up -d && cd airflow && docker compose up -d"
    if ($LASTEXITCODE -ne 0) { Fail "Nao consegui subir os containers (codigo $LASTEXITCODE)." }

    Write-Host "Esperando o Airflow responder..."
    $limite = (Get-Date).AddSeconds(240)
    while (-not (Test-Airflow)) {
        if ((Get-Date) -gt $limite) { Fail "O Airflow nao respondeu em $url a tempo." }
        Start-Sleep -Seconds 5
    }
}

Write-Host "Airflow no ar: $url" -ForegroundColor Green
if (-not $NoOpen) { Start-Process $url }
