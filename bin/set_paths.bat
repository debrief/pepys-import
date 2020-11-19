@echo off

REM Change to the directory that this batch file is in
REM storing the original directory so we can get back to it
set orig_path=%cd%
cd /D "%~dp0"
if ERRORLEVEL 1 goto :ERROR_CD


REM Get absolute path to folder with python executable in it
set PEPYS_PATH_PYTHON=..\python
pushd %PEPYS_PATH_PYTHON%
set PEPYS_PATH_PYTHON_ABS=%CD%
popd
if ERRORLEVEL 1 goto :ERROR_PYPATH

REM Get absolute path to folder with spatialite DLLs in it
set PEPYS_PATH_SPATIALITE=..\lib\spatialite-loadable-modules-5.0.0-win-amd64
pushd %PEPYS_PATH_SPATIALITE%
set PEPYS_PATH_SPATIALITE_ABS=%CD%
popd
if ERRORLEVEL 1 goto :ERROR_SLPATH

REM Set PATH env var to include those absolute paths
set PATH=%PEPYS_PATH_PYTHON_ABS%;%PEPYS_PATH_SPATIALITE_ABS%;%PATH%

REM Clear unneeded environment variables
set PEPYS_PATH_PYTHON=
set PEPYS_PATH_PYTHON_ABS=
set PEPYS_PATH_SPATIALITE=
set PEPYS_PATH_SPATIALITE_ABS=
if ERRORLEVEL 1 goto :ERROR_SETVARS

REM Go back to the directory the user was in before we ran this script
cd %orig_path%
if ERRORLEVEL 1 goto :ERROR_CD

echo Successfully set paths for Pepys

REM Go to the end of the file - ie. skip the labels below
goto :eof

:ERROR_CD
echo ERROR: Couldn't change to correct directory
goto :eof

:ERROR_PYPATH
echo ERROR: Cannot find Python path
goto :eof

:ERROR_SLPATH
echo ERROR: Cannot find spatialite path
goto :eof

:ERROR_SETVARS
echo ERROR: Couldn't set PATH variable or clear other variables
goto :eof