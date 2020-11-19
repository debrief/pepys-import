@ECHO off
powershell.exe -executionpolicy remotesigned -File install_pepys.ps1
IF ERRORLEVEL 1 GOTO :ERROR
ECHO Shortcuts created and PATH set
PAUSE

GOTO :eof

:ERROR
ECHO Error running install_pepys.ps1