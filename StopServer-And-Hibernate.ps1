# Gracefully stop Forge (via stop.flag) then hibernate
# Determine the directory that contains this script so paths are relative to
# the Minecraft server root.  This allows the script to be moved without
# editing hard-coded paths.
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$flag = Join-Path $dir "stop.flag"
$log  = Join-Path $dir "wrapper.log"

New-Item -Path $flag -ItemType File -Force | Out-Null

# Wait up to 3 minutes for the wrapper to log the exit
$deadline = (Get-Date).AddMinutes(3)
$stopped = $false
while ((Get-Date) -lt $deadline) {
    if (Test-Path $log -and (Select-String -Path $log -SimpleMatch "Server exited with code" -Quiet)) {
        $stopped = $true; break
    }
    Start-Sleep -Seconds 5
}
if (-not $stopped) { Write-Output "Timeout waiting for server; continuing to power down." }

# Hibernate (swap to shutdown in note below if desired)
shutdown.exe /h
