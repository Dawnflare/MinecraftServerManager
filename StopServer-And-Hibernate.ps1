# StopServer-And-Hibernate.ps1
# Gracefully stop the Forge server, run backup.bat, then hibernate.
# Run from Task Scheduler as SYSTEM with "Start in" set to the server folder.

# ------------------- CONFIG -------------------
$ServerDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$StopFlag    = Join-Path $ServerDir "stop.flag"
$BackupBat   = Join-Path $ServerDir "backup.bat"
$TimeoutSec  = 180      # how long to wait for the server to exit after stop.flag
$PollMillis  = 1000     # how often to poll for exit (ms)
$LogFile     = Join-Path $ServerDir "Stop-Hibernate.log"
# ----------------------------------------------

Set-Location $ServerDir

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    $line | Tee-Object -FilePath $LogFile -Append
}

# 1) Signal stop via stop.flag (manager watches for this)
try {
    Log "Creating stop.flag ..."
    "stop" | Out-File -FilePath $StopFlag -Encoding ascii -Force
} catch {
    Log "ERROR writing stop.flag: $($_.Exception.Message)"
}

# 2) Wait for the Java server process to exit
function IsServerRunning {
    $procs = Get-Process -Name "java","javaw" -ErrorAction SilentlyContinue
    foreach ($p in $procs) {
        try {
            $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)").CommandLine
            if ($cmd -and ($cmd -match "forge" -or $cmd -match "win_args\.txt" -or $cmd -match "fmlloader")) {
                return $true
            }
        } catch {}
    }
    return $false
}

$elapsed = 0
while ($elapsed -lt $TimeoutSec) {
    if (-not (IsServerRunning)) {
        Log "Server process is no longer running."
        break
    }
    Start-Sleep -Milliseconds $PollMillis
    $elapsed += [int]($PollMillis / 1000)
}
if ($elapsed -ge $TimeoutSec) {
    Log "WARNING: Timed out waiting ($TimeoutSec s) for server to exit. Proceeding anyway."
}

# 3) Run backup if present and server appears to be stopped
if (Test-Path $BackupBat) {
    if (-not (IsServerRunning)) {
        Log "Starting backup: $BackupBat"
        try {
            $psi = New-Object System.Diagnostics.ProcessStartInfo
            $psi.FileName = "cmd.exe"
            $psi.Arguments = "/c `"$BackupBat`""
            $psi.WorkingDirectory = $ServerDir
            $psi.RedirectStandardOutput = $true
            $psi.RedirectStandardError  = $true
            $psi.UseShellExecute = $false
            $p = [System.Diagnostics.Process]::Start($psi)
            $p.OutputDataReceived += { if ($_.Data) { Log "[backup] $($_.Data)" } }
            $p.ErrorDataReceived  += { if ($_.Data) { Log "[backup] $($_.Data)" } }
            $p.BeginOutputReadLine()
            $p.BeginErrorReadLine()
            $p.WaitForExit()
            Log "Backup finished with exit code $($p.ExitCode)."
        } catch {
            Log "ERROR running backup: $($_.Exception.Message)"
        }
    } else {
        Log "Skipped backup: server still running."
    }
} else {
    Log "No backup.bat found at $BackupBat (skipping backup)."
}

# 4) Close the minecraft_server_manager.pyw application so it can be relaunched later
Start-Sleep -Seconds 10
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like '*minecraft_server_manager.pyw*' } |
    ForEach-Object {
        Log "Closing manager process $($_.ProcessId)"
        Invoke-CimMethod -InputObject $_ -MethodName Terminate | Out-Null
    }

# 5) Hibernate
Log "Hibernating system ..."
try {
    powercfg /HIBERNATE ON | Out-Null
} catch {}
shutdown /h
