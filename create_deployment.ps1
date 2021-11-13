Write-Output "INFO: Starting to create Pepys deployment"

# Download embedded Python distribution
try {
    $url = 'https://www.python.org/ftp/python/3.9.8/python-3.9.8-embed-amd64.zip'
    (New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\python.zip")
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not download embedded Python - has the URL changed?"
    Exit 1
}

try {
    # Extract zip file
    Expand-Archive -Path python.zip -DestinationPath .\python -Force
    Write-Output "INFO: Downloaded and extracted embedded Python"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not extract Python zip file"
    Exit 1
}

try {
    # Download get-pip script
    $url = 'https://bootstrap.pypa.io/get-pip.py'
    (New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\get-pip.py")
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not download get-pip.py - has the URL changed?"
    Exit 1
}

# Try-Catch block catches error finding/running the exe file
# if ($LastExitCode) block catches error from the python.exe itself
try {
    # Install pip
    .\python\python.exe .\get-pip.py --no-warn-script-location 

    if ($LastExitCode -ne 0)
    {
        Write-Output "ERROR: Could not install pip"
        Exit 1
    }
    Write-Output "INFO: Installed pip"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not run Python to install pip"
    Exit 1
}

try {
    # Download SQLite DLL
    $url = 'https://www.sqlite.org/2020/sqlite-dll-win64-x64-3310100.zip'
    (New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\sqlite.zip")
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not download SQLite - has the URL changed?"
    Exit 1
}

try {
    # Extract SQLite DLL to Python folder, deliberately overwriting sqlite3.dll provided by Python
    # (note the -Force argument, to force overwriting)
    Expand-Archive -Path sqlite.zip -DestinationPath .\python -Force
    Write-Output "INFO: Downloaded and extracted SQLite"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not extract SQLite zip file"
    Exit 1
}

try {
    # Download mod_spatialite DLL files
    # This file is originally hosted at http://www.gaia-gis.it/gaia-sins/windows-bin-amd64/spatialite-loadable-modules-5.0.0-win-amd64.7z
    # but this keeps giving errors, which makes our CI fail
    # Therefore we've hosted it in the libs directory on our gh-pages branch, using the URL below
    $url = 'https://debrief.github.io/pepys-import/libs/spatialite-loadable-modules-5.0.0-win-amd64.7z'
    (New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\spatialite-loadable-modules-5.0.0-win-amd64.7z")
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not download Spatialite - has the URL changed?"
    Exit 1
}

try {
    # mod_spatialite comes in a 7zip archive, so we need to download 7zip to be able to extract it
    $url = 'http://www.7-zip.org/a/7za920.zip'
    (New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\7zip.zip")
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not download 7zip - has the URL changed?"
    Exit 1
}

try {
    # Put the 7zip exe in the .\7zip folder - we will delete this later
    Expand-Archive -Path 7zip.zip -DestinationPath .\7zip -Force
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not extract 7zip"
    Exit 1
}

try {
    # Extract the mod_spatialite 7zip file into the lib folder (it creates its own subfolder in there)
    .\7zip\7za.exe x .\spatialite-loadable-modules-5.0.0-win-amd64.7z -olib -y

    if ($LastExitCode -ne 0)
    {
        Write-Output "ERROR: Could not extract spatialiate"
        Exit 1
    }
    Write-Output "INFO: Downloaded and extracted mod_spatialite"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not run 7zip to extract spatialite"
    Exit 1
}


try {
    # Set the Python Path file to tell it where to find modules - including the new pip location and
    # the directory above the python folder (with pepys-import in it). This creates a ._pth file which
    # Python uses as it's *only* source for generating sys.path (ie. it does NOT take into account
    # environment variables such as PYTHONPATH)
    Set-Content -Encoding ascii .\python\python38._pth @"
python38.zip
.
Lib\site-packages
..
import site
"@

    Set-Content -Encoding ascii .\python\Lib\site-packages\extra_paths.pth @"
import sys; sys.path.insert(0, "")
pip\_vendor\pep517
"@


    Write-Output "INFO: Set Python pth files"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not write to path files"
    Exit 1
}

try {
    # Do a standard pip install of the requirements and dev requirements, not warning us that scripts will be unavailable
    .\python\python.exe -m pip install -r requirements.txt -r requirements_dev.txt --no-warn-script-location --no-cache-dir --use-deprecated=legacy-resolver

    if ($LastExitCode -ne 0)
    {
        Write-Output "ERROR: Problem installing dependencies using pip"
        Exit 1
    }

    Write-Output "INFO: Installed Python dependencies"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not run Python to install requirements using pip"
    Exit 1
}


try {
    Remove-Item *.zip
    Remove-Item *.7z
    Remove-Item get-pip.py

    Write-Output "INFO: Cleaned up all except 7zip"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not delete old deployment files"
    Exit 1
}


Write-Output "INFO: Building documentation"
try {
    # Write to the same folder that 'make html' does, so it works for devs who've done that on other platforms
    .\python\Scripts\sphinx-build.exe docs docs\_build\html

    if ($LastExitCode -ne 0)
    {
        Write-Output "ERROR: Problem running sphinx-build.exe to build docs"
        Exit 1
    }
    write-Output "INFO: Finished building documentation"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not run sphinx-build.exe to build docs"
    Exit 1
}

try {
    # Add the build date into the source code, so it can be displayed in the
    # welcome text
    $timestamp_str = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    (Get-Content .\pepys_import\__init__.py).replace('__build_timestamp__ = None', '__build_timestamp__ = "' + $timestamp_str + '"') | Set-Content .\pepys_import\__init__.py
    (Get-Content .\bin\set_title.bat).replace('BUILDTIMESTAMP', $timestamp_str) | Set-Content .\bin\set_title.bat

}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not set build timestamp in __init__.py"
    Exit 1
}

try {
    # Zip up whole folder into a zip-file with the current date in the filename
    # excluding the 7zip folder
    $date_str = Get-Date -Format "yyyyMMdd"
    $gitcommit = git rev-parse --short HEAD
    # Get the branch name from the GITHUB_HEAD_REF/GITHUB_REF env var if it exists (which it will if
    # we're running on GH Actions), otherwise use a git command (the git command doesn't
    # work on Github actions)
    if (Test-Path env:GITHUB_HEAD_REF) {
        $gitbranch = $env:GITHUB_HEAD_REF
    } elseif (Test-Path env:GITHUB_REF) {
        $gitbranch = $env:GITHUB_REF.Replace("refs/heads/", "").Replace("refs/tags/", "")
    } else {
        $gitbranch = git branch --show-current
    }
    
    $output_filename = "pepys_import-$date_str-$gitbranch-$gitcommit.zip".Replace("/", "-")

    .\7zip\7za.exe a .\$output_filename .\* -xr!7zip/ -xr!"bin\distlib-0.3.0-py2.py3-none-any.whl"

    if ($LastExitCode -ne 0)
    {
        Write-Output "ERROR: Error returned from running 7zip to create final deployment file"
        Exit 1
    }

    Write-Output "INFO: Written zipped deployment file to $output_filename"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not run 7zip to create final deployment file"
    Exit 1
}


try {
    # Remove folders/files that we don't need any more
    Remove-Item .\7zip -Recurse

    Write-Output "INFO: Finished cleanup"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not remove items in final cleanup"
    Exit 1
}
