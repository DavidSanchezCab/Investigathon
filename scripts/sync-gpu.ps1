[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$syncRepoRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$syncPrivateRoot = Join-Path $syncRepoRoot '.gpu-private'
$syncKey = Join-Path $syncPrivateRoot 'investigathon-gpu.key'
$syncKnownHosts = Join-Path $syncPrivateRoot 'known_hosts'
$syncBundle = Join-Path $syncPrivateRoot 'gpu-sync.bundle'
$syncHostSpec = 'ubuntu@18.227.123.98'
$syncExpectedOrigin = 'https://github.com/DavidSanchezCab/Investigathon'
$syncSshOptions = @('-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
    '-o', 'StrictHostKeyChecking=yes', '-o', "UserKnownHostsFile=$syncKnownHosts", '-i', $syncKey)
$syncStage = 'comprobaciones iniciales'

function Invoke-SyncNative {
    param(
        [Parameter(Mandatory = $true)][string]$Program,
        [Parameter(Mandatory = $true)][string[]]$NativeArguments,
        [Parameter(Mandatory = $true)][string]$Description,
        [int[]]$AllowedExitCodes = @(0),
        [string]$StdinText,
        [switch]$HasStdin
    )
    # Capture stderr as diagnostics, including on Windows PowerShell 5.1.
    $previousErrorAction = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        if ($HasStdin) {
            $nativeOutput = @($StdinText | & $Program @NativeArguments 2>&1)
        } else {
            $nativeOutput = @(& $Program @NativeArguments 2>&1)
        }
        $nativeExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorAction
    }
    $outputLines = @($nativeOutput | ForEach-Object { $_.ToString() })
    if ($nativeExitCode -notin $AllowedExitCodes) {
        throw "$Description falló (código $nativeExitCode).`n$($outputLines -join "`n")"
    }
    return [pscustomobject]@{ ExitCode = $nativeExitCode; Lines = $outputLines }
}

function Invoke-SyncGit {
    param([Parameter(Mandatory = $true)][string[]]$GitArguments)
    return Invoke-SyncNative -Program 'git' -NativeArguments (@('-C', $syncRepoRoot) + $GitArguments) `
        -Description 'Git en la PC'
}

function Get-SyncGitValue {
    param([Parameter(Mandatory = $true)][string[]]$GitArguments)
    $gitResult = Invoke-SyncGit -GitArguments $GitArguments
    if ($gitResult.Lines.Count -ne 1) {
        throw 'Git devolvió una respuesta inesperada; no se puede continuar con seguridad.'
    }
    return $gitResult.Lines[0].Trim()
}

function ConvertTo-SyncOrigin {
    param([string]$OriginUrl)
    $normalizedOrigin = $OriginUrl.Trim().TrimEnd('/')
    if ($normalizedOrigin.EndsWith('.git', [StringComparison]::Ordinal)) {
        $normalizedOrigin = $normalizedOrigin.Substring(0, $normalizedOrigin.Length - 4)
    }
    return $normalizedOrigin
}

function Assert-SyncLocalClean {
    if ((Get-SyncGitValue -GitArguments @('symbolic-ref', '--short', 'HEAD')) -cne 'main') {
        throw 'La PC debe estar en la rama main. Cambiá de rama y repetí la sincronización.'
    }
    $localStatus = Invoke-SyncGit -GitArguments @('status', '--porcelain', '--untracked-files=all')
    if ($localStatus.Lines.Count -ne 0) {
        throw 'La PC tiene cambios sin commit. Revisalos y hacé commit antes de sincronizar; el helper no los guarda automáticamente.'
    }
}

function Test-SyncAncestor {
    param([string]$Ancestor, [string]$Descendant)
    $ancestorResult = Invoke-SyncNative -Program 'git' -NativeArguments @('-C', $syncRepoRoot,
        'merge-base', '--is-ancestor', $Ancestor, $Descendant) -AllowedExitCodes @(0, 1) `
        -Description 'Comprobación de ancestros Git'
    return $ancestorResult.ExitCode -eq 0
}

function Invoke-SyncRemote {
    param(
        [Parameter(Mandatory = $true)][string]$Body,
        [string[]]$CommitArguments = @()
    )
    # The remote command is static except for validated hexadecimal object IDs.
    # Windows PowerShell can append CRLF to piped stdin; Bash needs LF.
    $remoteCommand = "tr -d '\r' | bash -s --"
    foreach ($commitArgument in $CommitArguments) {
        if ($commitArgument -cnotmatch '^[0-9a-f]{40}([0-9a-f]{24})?$') {
            throw 'Se rechazó un identificador de commit inválido.'
        }
        $remoteCommand += " '$commitArgument'"
    }
    $remoteResult = Invoke-SyncNative -Program 'ssh' `
        -NativeArguments (@('-T') + $syncSshOptions + @($syncHostSpec, $remoteCommand)) `
        -Description 'Operación Git en la GPU' -HasStdin `
        -StdinText (($syncRemoteCommon + "`n" + $Body) -replace "`r`n", "`n")
    $reportedHeads = @()
    foreach ($remoteLine in $remoteResult.Lines) {
        if ($remoteLine -cmatch '^GPU_SYNC_HEAD=([0-9a-f]{40}([0-9a-f]{24})?)$') {
            $reportedHeads += $Matches[1]
        }
    }
    if ($reportedHeads.Count -ne 1) {
        throw 'La GPU no devolvió un HEAD verificable; se detuvo la sincronización.'
    }
    return $reportedHeads[0]
}

$syncRemoteCommon = @'
set -euo pipefail
umask 077
sync_repo="$HOME/investigathon"
sync_fail() { printf 'GPU: %s\n' "$1" >&2; exit 1; }
[[ -d "$sync_repo/.git" ]] || sync_fail 'Falta el repositorio Git en ~/investigathon.'
sync_expected_root="$(cd "$sync_repo" && pwd -P)"
sync_actual_root="$(git -C "$sync_repo" rev-parse --show-toplevel)"
[[ "$sync_actual_root" == "$sync_expected_root" ]] || sync_fail 'La raiz Git remota no coincide con ~/investigathon.'
sync_origin="$(git -C "$sync_repo" remote get-url origin)"
sync_origin="${sync_origin%/}"
sync_origin="${sync_origin%.git}"
[[ "$sync_origin" == 'https://github.com/DavidSanchezCab/Investigathon' ]] || sync_fail 'El origin remoto no es el repositorio esperado.'
[[ "$(git -C "$sync_repo" symbolic-ref --short HEAD)" == main ]] || sync_fail 'La GPU debe estar en la rama main.'
sync_assert_clean() {
    [[ -z "$(git -C "$sync_repo" status --porcelain --untracked-files=all)" ]] || sync_fail 'Hay cambios sin commit en la GPU. Revisarlos y hacer commit antes de sincronizar.'
}
sync_assert_clean
'@

$syncPrepareBundle = @'
sync_head="$(git -C "$sync_repo" rev-parse HEAD)"
git -C "$sync_repo" bundle create "$sync_repo/.git/gpu-sync.bundle" main
[[ "$(git -C "$sync_repo" rev-parse HEAD)" == "$sync_head" ]] || sync_fail 'main cambio mientras se preparaba el bundle. Repetir la sincronizacion.'
sync_assert_clean
printf 'GPU_SYNC_HEAD=%s\n' "$sync_head"
'@

$syncCheckRemoteHead = @'
sync_head="$(git -C "$sync_repo" rev-parse HEAD)"
[[ "$sync_head" == "$1" ]] || sync_fail 'La GPU cambio durante la sincronizacion. No se sobrescribio nada; repetirla.'
printf 'GPU_SYNC_HEAD=%s\n' "$sync_head"
'@

$syncFastForwardRemote = @'
[[ "$(git -C "$sync_repo" rev-parse HEAD)" == "$1" ]] || sync_fail 'La GPU recibio otro commit; no se sobrescribio nada. Repetir la sincronizacion.'
git -C "$sync_repo" fetch origin refs/heads/main:refs/remotes/origin/main
[[ "$(git -C "$sync_repo" rev-parse refs/remotes/origin/main)" == "$2" ]] || sync_fail 'GitHub cambio durante la sincronizacion. No se sobrescribio nada; repetirla.'
sync_assert_clean
[[ "$(git -C "$sync_repo" rev-parse HEAD)" == "$1" ]] || sync_fail 'La GPU cambio durante el fetch; repetir la sincronizacion.'
git -C "$sync_repo" merge --ff-only refs/remotes/origin/main
sync_assert_clean
sync_head="$(git -C "$sync_repo" rev-parse HEAD)"
[[ "$sync_head" == "$2" ]] || sync_fail 'El HEAD final de la GPU no coincide con el esperado.'
printf 'GPU_SYNC_HEAD=%s\n' "$sync_head"
'@

try {
    foreach ($requiredProgram in @('git', 'ssh', 'scp')) {
        if (!(Get-Command $requiredProgram -ErrorAction SilentlyContinue)) {
            throw "Falta el programa $requiredProgram en la PC."
        }
    }
    if (!(Test-Path -LiteralPath $syncKey -PathType Leaf) -or
        !(Test-Path -LiteralPath $syncKnownHosts -PathType Leaf)) {
        throw 'Faltan la clave SSH o known_hosts en .gpu-private. No se omite la verificación del servidor.'
    }
    $actualLocalRoot = [IO.Path]::GetFullPath((Get-SyncGitValue -GitArguments @('rev-parse', '--show-toplevel')))
    if ($actualLocalRoot.TrimEnd('\', '/') -ine $syncRepoRoot.TrimEnd('\', '/')) {
        throw 'La raíz Git local no coincide con el proyecto que contiene este script.'
    }
    $localOrigin = Get-SyncGitValue -GitArguments @('remote', 'get-url', 'origin')
    if ((ConvertTo-SyncOrigin $localOrigin) -cne $syncExpectedOrigin) {
        throw 'El origin local no es el repositorio esperado. No se modificó su configuración.'
    }
    $localPushUrls = Invoke-SyncGit -GitArguments @('remote', 'get-url', '--push', '--all', 'origin')
    foreach ($pushUrl in $localPushUrls.Lines) {
        if ((ConvertTo-SyncOrigin $pushUrl) -cne $syncExpectedOrigin) {
            throw 'El destino de push de origin no es el repositorio esperado. No se publicará nada.'
        }
    }
    Assert-SyncLocalClean
    $initialLocalHead = Get-SyncGitValue -GitArguments @('rev-parse', 'HEAD')

    $syncStage = 'lectura de GitHub y preparación del bundle GPU'
    Write-Host 'Leyendo GitHub y los commits de la GPU...'
    $null = Invoke-SyncGit -GitArguments @('fetch', 'origin', 'refs/heads/main:refs/remotes/origin/main')
    $originHead = Get-SyncGitValue -GitArguments @('rev-parse', 'refs/remotes/origin/main')
    $initialGpuHead = Invoke-SyncRemote -Body $syncPrepareBundle
    $null = Invoke-SyncNative -Program 'scp' `
        -NativeArguments ($syncSshOptions + @("${syncHostSpec}:~/investigathon/.git/gpu-sync.bundle", $syncBundle)) `
        -Description 'Copia del bundle de commits GPU'
    $null = Invoke-SyncGit -GitArguments @('fetch', $syncBundle, 'main:refs/remotes/gpu/main')
    $bundledGpuHead = Get-SyncGitValue -GitArguments @('rev-parse', 'refs/remotes/gpu/main')
    if ($bundledGpuHead -cne $initialGpuHead) {
        throw 'El bundle no coincide con el HEAD capturado en la GPU. No se movió main.'
    }

    $syncStage = 'comprobación de compatibilidad sin mover main'
    $syncHeads = @($initialLocalHead, $originHead, $bundledGpuHead) | Select-Object -Unique
    $targetHead = $null
    foreach ($candidateHead in $syncHeads) {
        $containsAllHeads = $true
        foreach ($otherHead in $syncHeads) {
            if (!(Test-SyncAncestor -Ancestor $otherHead -Descendant $candidateHead)) {
                $containsAllHeads = $false
                break
            }
        }
        if ($containsAllHeads) {
            $targetHead = $candidateHead
            break
        }
    }
    if (!$targetHead) {
        throw 'Las historias de PC, GitHub y GPU divergen. No se movió main en ninguna máquina ni se perdió nada. Reconciliá los commits manualmente usando origin/main y gpu/main y volvé a ejecutar el helper; no se hará reset, stash ni push forzado.'
    }
    Assert-SyncLocalClean
    if ((Get-SyncGitValue -GitArguments @('rev-parse', 'HEAD')) -cne $initialLocalHead) {
        throw 'La PC recibió otro commit durante las comprobaciones. Repetí la sincronización.'
    }
    $null = Invoke-SyncRemote -Body $syncCheckRemoteHead -CommitArguments @($initialGpuHead)

    $syncStage = 'avance local y publicación desde la PC'
    $null = Invoke-SyncGit -GitArguments @('merge', '--ff-only', $targetHead)
    Assert-SyncLocalClean
    if ((Get-SyncGitValue -GitArguments @('rev-parse', 'HEAD')) -cne $targetHead) {
        throw 'El HEAD local cambió antes del push. Revisá los commits y repetí la sincronización.'
    }
    $null = Invoke-SyncGit -GitArguments @('push', 'origin', 'main')

    $syncStage = 'avance de la GPU y verificación final'
    $finalGpuHead = Invoke-SyncRemote -Body $syncFastForwardRemote -CommitArguments @($initialGpuHead, $targetHead)
    $null = Invoke-SyncGit -GitArguments @('fetch', 'origin', 'refs/heads/main:refs/remotes/origin/main')
    Assert-SyncLocalClean
    $finalLocalHead = Get-SyncGitValue -GitArguments @('rev-parse', 'HEAD')
    $finalOriginHead = Get-SyncGitValue -GitArguments @('rev-parse', 'refs/remotes/origin/main')
    $verifiedGpuHead = Invoke-SyncRemote -Body $syncCheckRemoteHead -CommitArguments @($finalGpuHead)
    if ($finalLocalHead -cne $targetHead -or $finalOriginHead -cne $targetHead -or $verifiedGpuHead -cne $targetHead) {
        throw 'Los HEAD finales no coinciden; hubo cambios concurrentes. No se perdió ningún commit. Revisá el estado y repetí el helper.'
    }
    Write-Host "PC, GitHub y GPU sincronizados en $targetHead. Ambos árboles están limpios."
} catch {
    Write-Error "Sincronización detenida en: $syncStage.`n$($_.Exception.Message)`nNo se borraron commits ni se forzó ninguna rama. Los commits que ya se hubieran publicado o incorporado se conservan." -ErrorAction Continue
    exit 1
}
