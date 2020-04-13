@echo off
CALL set_paths.bat
REM note: when we're called via the "SendTo" link, the target is in the first argument
python -m pepys_import.import --path %1 %2 %3 %4 %5 %6 %7 %8
REM we're pausing the end of the script so we learn more about what is being processed
PAUSE
