param(
    [ValidateSet('ssh', 'check', 'upload', 'bootstrap', 'smoke', 'download')]
    [string]$Action = 'check'
)
$ErrorActionPreference = 'Stop'
$gpuRoot = Split-Path -Parent $PSScriptRoot
$gpuPrivate = Join-Path $gpuRoot '.gpu-private'
$gpuKey = Join-Path $gpuPrivate 'investigathon-gpu.key'
$gpuKnownHosts = Join-Path $gpuPrivate 'known_hosts'
if (!(Test-Path -LiteralPath $gpuKey) -or !(Test-Path -LiteralPath $gpuKnownHosts)) {
    throw 'Faltan los adjuntos privados del mail en .gpu-private. Ver docs/GPU.md.'
}
$gpuSshOptions = @('-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
    '-o', 'StrictHostKeyChecking=yes', '-o', "UserKnownHostsFile=$gpuKnownHosts", '-i', $gpuKey)
$gpuRemote = 'ubuntu@18.227.123.98'
function Invoke-GpuSsh([string]$RemoteCommand) {
    & ssh @gpuSshOptions $gpuRemote $RemoteCommand
    if ($LASTEXITCODE -ne 0) { throw "SSH termino con codigo $LASTEXITCODE" }
}
function Copy-GpuScripts {
    Invoke-GpuSsh 'mkdir -p ~/investigathon/gpu ~/investigathon/logs ~/investigathon/results'
    $gpuFiles = Get-ChildItem -LiteralPath (Join-Path $gpuRoot 'gpu') -File |
        Where-Object { $_.Extension -in '.py', '.sh', '.txt' } |
        Select-Object -ExpandProperty FullName
    & scp @gpuSshOptions @gpuFiles "${gpuRemote}:~/investigathon/gpu/"
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron subir los scripts' }
}
switch ($Action) {
    'ssh' { & ssh @gpuSshOptions -t $gpuRemote }
    'check' {
        Invoke-GpuSsh 'nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv; free -h; df -h /; cat ~/investigathon/setup-status.txt 2>/dev/null; tail -n 12 ~/investigathon/logs/bootstrap.log 2>/dev/null; true'
    }
    'upload' { Copy-GpuScripts }
    'bootstrap' {
        Copy-GpuScripts
        Invoke-GpuSsh 'nohup bash ~/investigathon/gpu/bootstrap.sh >> ~/investigathon/logs/bootstrap.log 2>&1 < /dev/null &'
        Write-Output 'Instalacion iniciada. Consultar .\scripts\gpu.ps1 check'
    }
    'smoke' {
        Invoke-GpuSsh '~/investigathon/.venv/bin/python ~/investigathon/gpu/smoke_test.py'
    }
    'download' {
        $gpuResults = Join-Path $gpuPrivate 'results'
        New-Item -ItemType Directory -Path $gpuResults -Force | Out-Null
        & scp @gpuSshOptions -r "${gpuRemote}:~/investigathon/results/." $gpuResults
        if ($LASTEXITCODE -ne 0) { throw 'No se pudieron descargar los resultados' }
        & scp @gpuSshOptions "${gpuRemote}:~/investigathon/models-manifest.json" $gpuResults
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo descargar el manifiesto' }
        Write-Output "Resultados en $gpuResults"
    }
}
