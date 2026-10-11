# Cria na area de trabalho o atalho "Airflow", que roda o iniciar-airflow.ps1 desta pasta.
# Rode de novo se mover o repositorio de lugar: o atalho e refeito apontando para o caminho novo.
#
#   -PastaWsl   pasta do lab-dados dentro do Ubuntu (WSL), de onde os containers sobem
param([string]$PastaWsl = '~/projetos/lab-dados')

$script = Join-Path $PSScriptRoot 'iniciar-airflow.ps1'
$desktop = [Environment]::GetFolderPath('Desktop')
$icone = Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe'

$atalho = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desktop 'Airflow.lnk'))
$atalho.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$atalho.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$script`" -PastaWsl `"$PastaWsl`""
$atalho.WorkingDirectory = $PSScriptRoot
if (Test-Path $icone) { $atalho.IconLocation = "$icone,0" }
$atalho.Description = 'Abre o Airflow (sobe o Docker e os containers se estiverem parados)'
$atalho.Save()

Write-Host "Atalho criado em $desktop\Airflow.lnk"
