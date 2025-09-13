@echo off
set backupDir=C:\Backups\MinecraftBackups
set worldDir=C:\Users\<user>\Minecraft\<server folder>\world

:: Make sure backup folder exists
if not exist "%backupDir%" mkdir "%backupDir%"

:: Create timestamp (YYYY-MM-DD_HH-MM-SS)
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value') do set datetime=%%a
set timestamp=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%-%datetime:~12,2%

:: Create backup zip
powershell Compress-Archive -Path "%worldDir%" -DestinationPath "%backupDir%\minecraftserver_%timestamp%.zip"

:: Keep only last 10 backups, delete older ones
for /f "skip=10 eol=: delims=" %%F in ('dir /b /o-d "%backupDir%\world_*.zip"') do del "%backupDir%\%%F"


echo Backup created: %backupDir%\world_%timestamp%.zip
