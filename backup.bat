@echo off

REM ===== User Configuration =====
REM Set backupDir to override the default backup save folder.
REM Example: set "backupDir=D:\Backups\Minecraft"
set "backupDir="
REM ===== End User Configuration =====

cd /d "%~dp0"

set "worldDir=%cd%\world"
if not defined backupDir set "backupDir=%cd%\backups"

:: Make sure backup folder exists
if not exist "%backupDir%" mkdir "%backupDir%"

:: Create timestamp (YYYY-MM-DD_HH-MM-SS)
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value') do set datetime=%%a
set timestamp=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%-%datetime:~12,2%

:: Create backup zip
powershell Compress-Archive -Path "%worldDir%" -DestinationPath "%backupDir%\world_%timestamp%.zip"

:: Keep only last 10 backups, delete older ones
for /f "skip=10 eol=: delims=" %%F in ('dir /b /o-d "%backupDir%\world_*.zip"') do del "%backupDir%\%%F"

echo Backup created: %backupDir%\world_%timestamp%.zip
