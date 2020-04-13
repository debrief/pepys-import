@echo off

REM Change to the directory that this batch file is in
REM storing the original directory so we can get back to it
set orig_path=%cd%
cd /D "%~dp0"


REM Get absolute path to folder with python executable in it
set PEPYS_PATH_PYTHON=..\python
pushd %PEPYS_PATH_PYTHON%
set PEPYS_PATH_PYTHON_ABS=%CD%
popd

REM Get absolute path to folder with spatialite DLLs in it
set PEPYS_PATH_SPATIALITE=..\lib\mod_spatialite-NG-win-amd64
pushd %PEPYS_PATH_SPATIALITE%
set PEPYS_PATH_SPATIALITE_ABS=%CD%
popd

REM Set PATH env var to include those absolute paths
set PATH=%PEPYS_PATH_PYTHON_ABS%;%PEPYS_PATH_SPATIALITE_ABS%;%PATH%

REM Clear unneeded environment variables
set PEPYS_PATH_PYTHON=
set PEPYS_PATH_PYTHON_ABS=
set PEPYS_PATH_SPATIALITE=
set PEPYS_PATH_SPATIALITE_ABS=

REM Go back to the directory the user was in before we ran this script
cd %orig_path%

echo Successfully set paths for pepys-import