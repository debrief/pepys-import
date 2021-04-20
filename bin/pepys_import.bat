@echo off
CALL set_title.bat Pepys Import
CALL set_paths.bat
REM If error returned from set_paths.bat then don't continue with running python
IF ERRORLEVEL 1 GOTO :ERROR
python -m pepys_import.cli %1 %2 %3 %4 %5 %6 %7 %8 %9

REM Go to the end of the file, skipping the :ERROR label below
GOTO :eof

REM PAUSE so that the user can see the error
:ERROR
PAUSE