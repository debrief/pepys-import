@echo off
CALL set_title.bat Pepys Import (training)
CALL set_paths.bat
REM If error returned from set_paths.bat then don't continue with running python
IF ERRORLEVEL 1 GOTO :ERROR

REM note: when we're called via the "SendTo" link, the target is in the first argument
python -m pepys_import.cli --training --path %1 %2 %3 %4 %5 %6 %7 %8
REM we're pausing the end of the script so we learn more about what is being processed
PAUSE

REM Go to the end of the file, skipping the :ERROR label below
GOTO :eof

REM PAUSE so that the user can see the error
:ERROR
PAUSE
