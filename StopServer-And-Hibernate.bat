@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ====== CONFIG ======
set "SERVER_DIR=C:\Users\saged\Minecraft\IceAndFireServer"
set "STOP_FLAG=%SERVER_DIR%\stop.flag"
set "WRAP_LOG=%SERVER_DIR%\wrapper.log"
set "BACKUP_BAT=%SERVER_DIR%\backup.bat"
set "LOG_FILE=%SERVER_DIR%\Stop-Hibernate.log"
set "TIMEOUT_SEC=180"   rem how long to wait for clean stop
set "SLEEP_STEP=5"      rem poll every 5 seconds
rem =====================

cd /d "%SERVER_DIR%" || goto :eof

call :log Creating stop.flag …
> "%STOP_FLAG%" echo stop

rem ---- wait for server to exit (look for the manager’s final line) ----
set /a waited=0
:wait_loop
findstr /c:"Server exited with code" "%WRAP_LOG%" >nul 2>&1
if %errorlevel%==0 (
  call :log Detected clean exit in wrapper.log.
  goto after_wait
)
if %waited% GEQ %TIMEOUT_SEC% (
  call :log WARNING: Timed out waiting %TIMEOUT_SEC%s for server to stop. Proceeding.
  goto after_wait
)
timeout /t %SLEEP_STEP% /nobreak >nul
set /a waited+=SLEEP_STEP
goto wait_loop

:after_wait
rem ---- run backup if present ----
if exist "%BACKUP_BAT%" (
  call :log Starting backup: "%BACKUP_BAT%"
  call "%BACKUP_BAT%" >> "%LOG_FILE%" 2>&1
  set "rc=%ERRORLEVEL%"
  call :log Backup finished with exit code %rc%.
) else (
  call :log No backup.bat found (skipping backup).
)

rem ---- enable hibernation (no-op if already enabled) and hibernate ----
call :log Hibernating system …
powercfg /HIBERNATE ON >nul 2>&1
shutdown /h
goto :eof

:log
>> "%LOG_FILE%" echo [%date% %time%] %*
exit /b
