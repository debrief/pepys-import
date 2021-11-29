@ECHO off
CALL set_title.bat Upgrade Pepys
CALL set_paths.bat

powershell.exe -executionpolicy remotesigned -File upgrade_pepys.ps1
IF ERRORLEVEL 1 GOTO :ERROR
ECHO Pepys Upgrade completed
PAUSE

GOTO :eof

:ERROR
ECHO Error running upgrade_pepys.ps1