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
    if (Test-Path $log) {
        try {
            $stream = [System.IO.File]::Open($log, [System.IO.FileMode]::Open,
                [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
            try {
                $reader = New-Object System.IO.StreamReader($stream)
                $txt = $reader.ReadToEnd()
            } finally {
                $reader.Dispose(); $stream.Dispose()
            }
            if ($txt -like '*Server exited with code*') { $stopped = $true; break }
        } catch {
            # Ignore file access issues and retry
        }
    }
    Start-Sleep -Seconds 5
}
if (-not $stopped) { Write-Output "Timeout waiting for server; continuing to power down." }

# Allow the user to see the GUI has stopped before closing the manager
Start-Sleep -Seconds 10

# Close the minecraft_server_manager.pyw application so it can be relaunched later
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like '*minecraft_server_manager.pyw*' } |
    ForEach-Object { Invoke-CimMethod -InputObject $_ -MethodName Terminate | Out-Null }

# Hibernate (swap to shutdown in note below if desired)
shutdown.exe /h
