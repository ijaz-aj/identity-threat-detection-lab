# fix_docker_stale_sockets.ps1
#
# Works around a known Docker Desktop bug on Windows (docker/desktop-feedback #460, #531, #786):
# after an unclean exit, Docker's AF_UNIX socket files become undeletable (Windows error 1920),
# and Docker Desktop crashes on the next start with
#   "remove ...\dockerInference: The file cannot be accessed by the system."
#
# Deleting the socket files fails, but renaming the folder that holds them works.
# This script:
#   1. waits until every Docker Desktop process has exited (you click Quit first),
#   2. renames each socket folder that still contains a socket file (nothing is deleted),
#   3. starts Docker Desktop and waits for the engine.
#
# Usage (PowerShell):  .\scripts\fix_docker_stale_sockets.ps1

$ErrorActionPreference = 'Stop'

$socketFolders = @(
    "$env:LOCALAPPDATA\Docker\run",
    "$env:LOCALAPPDATA\docker-secrets-engine"
)
$dockerExe = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'

# 1. Make sure Docker Desktop is fully closed (renaming while it runs would fail or break it).
#    After this crash, clicking Quit closes the dialog but the crashed backend keeps running,
#    so we give it 20 seconds to exit on its own, then force-stop it. Any socket files the
#    force-stop leaves behind are moved out of the way in step 2.
$dockerProcesses = 'Docker Desktop', 'com.docker.backend', 'com.docker.build'
$deadline = (Get-Date).AddSeconds(20)
while ((Get-Process -Name $dockerProcesses -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 2
}
$stillRunning = Get-Process -Name $dockerProcesses -ErrorAction SilentlyContinue
if ($stillRunning) {
    Write-Host "Force-stopping $($stillRunning.Count) crashed Docker process(es)..."
    $stillRunning | Stop-Process -Force
    Start-Sleep -Seconds 3
}
if (Get-Process -Name $dockerProcesses -ErrorAction SilentlyContinue) {
    throw 'Docker Desktop processes are still running. Close Docker from the tray icon, then run this again.'
}
Write-Host 'Docker Desktop has exited.'

# 2. Rename every socket folder that contains a socket file (shown as a ReparsePoint).
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
foreach ($folder in $socketFolders) {
    if (-not (Test-Path -LiteralPath $folder)) { continue }
    $sockets = Get-ChildItem -LiteralPath $folder -Force -Attributes ReparsePoint -ErrorAction SilentlyContinue
    if ($sockets) {
        $newName = (Split-Path $folder -Leaf) + ".stale-$stamp"
        Rename-Item -LiteralPath $folder -NewName $newName
        Write-Host "Renamed $folder -> $newName ($($sockets.Count) stale socket file(s))"
    }
}

# 3. Start Docker Desktop and wait up to 2 minutes for the Linux engine.
Start-Process -FilePath $dockerExe
Write-Host 'Starting Docker Desktop...'
$deadline = (Get-Date).AddMinutes(2)
do {
    Start-Sleep -Seconds 5
    $osType = docker info --format '{{.OSType}}' 2>$null
} until ($osType -eq 'linux' -or (Get-Date) -gt $deadline)

if ($osType -eq 'linux') {
    Write-Host 'Docker engine is running (Linux containers).'
} else {
    Write-Host 'Docker engine did not come up within 2 minutes. If an error dialog shows, click Quit and run this script again.'
    exit 1
}
