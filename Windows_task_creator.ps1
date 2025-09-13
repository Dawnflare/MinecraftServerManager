<#
Windows Task Creator
--------------------
Instructions:
- Place this script in the same directory as minecraft_server_manager.pyw and StopServer-And-Hibernate.ps1.
- Modify the configuration variables below to set your desired task times.
- Run this script from an elevated PowerShell prompt (Run as Administrator) to create the tasks.
- By default, existing tasks starting with "MinecraftServerManager" will be removed before new tasks are registered.
#>

# --- User Configuration ---

$DailyStartTime   = "06:00"  # Daily start time
$MTThFStartTime   = "14:30"  # Monday, Tuesday, Thursday, Friday start time
$WedStartTime     = "13:15"  # Wednesday start time
$WeekdayStopTime  = "08:00"  # Weekday stop time
$DailyStopTime    = "00:00"  # Daily stop time
$RemoveExistingTasks = $true  # Remove existing MinecraftServerManager* tasks?

# --- Derived Paths ---

$ServerRoot  = $PSScriptRoot
$ManagerPyw  = Join-Path $ServerRoot "minecraft_server_manager.pyw"
$StopScript  = Join-Path $ServerRoot "StopServer-And-Hibernate.ps1"

# --- Common actions/principals/settings ---

$pywExe  = Join-Path $env:SystemRoot "pyw.exe"
$psExe   = "powershell.exe"

$startAction = New-ScheduledTaskAction -Execute $pywExe -Argument "`"$ManagerPyw`"" -WorkingDirectory $ServerRoot
$stopAction  = New-ScheduledTaskAction -Execute $psExe -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StopScript`"" -WorkingDirectory $ServerRoot

$startPrincipal  = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$systemPrincipal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

$setStart = New-ScheduledTaskSettingsSet -WakeToRun:$true -AllowStartIfOnBatteries:$true -DisallowStartIfOnBatteries:$false
$setStop  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries:$true -DisallowStartIfOnBatteries:$false

# --- Remove existing tasks if requested ---

$TaskPrefix = "MinecraftServerManager"
if ($RemoveExistingTasks) {
    Get-ScheduledTask | Where-Object { $_.TaskName -like "$TaskPrefix*" } | ForEach-Object {
        Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false
    }
}

# --- Triggers ---

$trig_start_daily  = New-ScheduledTaskTrigger -Daily -At $DailyStartTime
$trig_start_mtthf  = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Thursday,Friday -At $MTThFStartTime
$trig_start_wed    = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Wednesday -At $WedStartTime
$trig_stop_weekday = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $WeekdayStopTime
$trig_stop_daily   = New-ScheduledTaskTrigger -Daily -At $DailyStopTime

$opt = @{ Force = $true }

# --- Register tasks ---

Register-ScheduledTask -TaskName "$TaskPrefix Start Daily $DailyStartTime" \
  -Action $startAction -Trigger $trig_start_daily -Principal $startPrincipal -Settings $setStart \
  -Description "Wake and start server manager (auto-starts server)" @opt

Register-ScheduledTask -TaskName "$TaskPrefix Start MonTueThuFri $MTThFStartTime" \
  -Action $startAction -Trigger $trig_start_mtthf -Principal $startPrincipal -Settings $setStart \
  -Description "Wake and start server manager (auto-starts server)" @opt

Register-ScheduledTask -TaskName "$TaskPrefix Start Wed $WedStartTime" \
  -Action $startAction -Trigger $trig_start_wed -Principal $startPrincipal -Settings $setStart \
  -Description "Wake and start server manager (auto-starts server)" @opt

Register-ScheduledTask -TaskName "$TaskPrefix Stop Weekdays $WeekdayStopTime (Hibernate)" \
  -Action $stopAction -Trigger $trig_stop_weekday -Principal $systemPrincipal -Settings $setStop \
  -Description "Graceful stop via stop.flag, wait for exit, then hibernate" @opt

Register-ScheduledTask -TaskName "$TaskPrefix Stop Daily $DailyStopTime (Hibernate)" \
  -Action $stopAction -Trigger $trig_stop_daily -Principal $systemPrincipal -Settings $setStop \
  -Description "Graceful stop via stop.flag, wait for exit, then hibernate" @opt

Write-Host "All tasks created. Verify wake timers are enabled in Power Options."
