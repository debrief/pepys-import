Write-Output "INFO: Starting to create Pepys deployment"

# Download embedded Python distribution
try {
    $url = 'https://www.python.org/ftp/python/3.7.6/python-3.7.6-embed-amd64.zip'
    (New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\python.zip")
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not download embedded Python - has the URL changed?"
    Exit
}

try {
    # Extract zip file
    Expand-Archive -Path python.zip -DestinationPath .\python -Force
    Write-Output "INFO: Downloaded and extracted embedded Python"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not extract Python zip file"
    Exit
}

try {
    # Download get-pip script
    $url = 'https://bootstrap.pypa.io/get-pip.py'
    (New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\get-pip.py")
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not download get-pip.py - has the URL changed?"
    Exit
}

# Try-Catch block catches error finding/running the exe file
# if ($LastExitCode) block catches error from the python.exe itself
try {
    # Install pip
    .\python\python.exe .\get-pip.py --no-warn-script-location 

    if ($LastExitCode -ne 0)
    {
        Write-Output "ERROR: Could not install pip"
        Exit
    }
    Write-Output "INFO: Installed pip"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not run Python to install pip"
    Exit
}

try {
    # Download SQLite DLL
    $url = 'https://www.sqlite.org/2020/sqlite-dll-win64-x64-3310100.zip'
    (New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\sqlite.zip")
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not download SQLite - has the URL changed?"
    Exit
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
    Exit
}

try {
    # Download mod_spatialite DLL files
    $url = 'http://www.gaia-gis.it/gaia-sins/windows-bin-amd64/spatialite-loadable-modules-5.0.0-win-amd64.7z'
    (New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\spatialite-loadable-modules-5.0.0-win-amd64.7z")
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not download Spatialite - has the URL changed?"
    Exit
}

try {
    # mod_spatialite comes in a 7zip archive, so we need to download 7zip to be able to extract it
    $url = 'http://www.7-zip.org/a/7za920.zip'
    (New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\7zip.zip")
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not download 7zip - has the URL changed?"
    Exit
}

try {
    # Put the 7zip exe in the .\7zip folder - we will delete this later
    Expand-Archive -Path 7zip.zip -DestinationPath .\7zip -Force
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not extract 7zip"
    Exit
}

try {
    # Extract the mod_spatialite 7zip file into the lib folder (it creates its own subfolder in there)
    .\7zip\7za.exe x .\spatialite-loadable-modules-5.0.0-win-amd64.7z -olib -y

    if ($LastExitCode -ne 0)
    {
        Write-Output "ERROR: Could not extract spatialiate"
        Exit
    }
    Write-Output "INFO: Downloaded and extracted mod_spatialite"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not run 7zip to extract spatialite"
    Exit
}


try {
    # Set the Python Path file to tell it where to find modules - including the new pip location and
    # the directory above the python folder (with pepys-import in it). This creates a ._pth file which
    # Python uses as it's *only* source for generating sys.path (ie. it does NOT take into account
    # environment variables such as PYTHONPATH)
    Set-Content -Encoding ascii .\python\python37._pth @"
python37.zip
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
    Exit
}

try {
    # Do a standard pip install of the requirements and dev requirements, not warning us that scripts will be unavailable
    .\python\python.exe -m pip install -r requirements.txt -r requirements_dev.txt --no-warn-script-location --no-cache-dir

    if ($LastExitCode -ne 0)
    {
        Write-Output "ERROR: Problem installing dependencies using pip"
        Exit
    }

    Write-Output "INFO: Installed Python dependencies"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not run Python to install requirements using pip"
    Exit
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
    Exit
}


Write-Output "INFO: Building documentation"
try {
    # Write to the same folder that 'make html' does, so it works for devs who've done that on other platforms
    .\python\Scripts\sphinx-build.exe docs docs\_build\html

    if ($LastExitCode -ne 0)
    {
        Write-Output "ERROR: Problem running sphinx-build.exe to build docs"
        Exit
    }
    write-Output "INFO: Finished building documentation"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not run sphinx-build.exe to build docs"
    Exit
}

try {
    # Zip up whole folder into a zip-file with the current date in the filename
    # excluding the 7zip folder
    $date_str = Get-Date -Format "yyyyMMdd"
    $output_filename = $date_str + "_pepys-import.zip"
    .\7zip\7za.exe a .\$output_filename .\* -xr!7zip/ -xr!"bin\distlib-0.3.0-py2.py3-none-any.whl"

    if ($LastExitCode -ne 0)
    {
        Write-Output "ERROR: Error returned from running 7zip to create final deployment file"
        Exit
    }

    Write-Output "INFO: Written zipped deployment file to $output_filename"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not run 7zip to create final deployment file"
    Exit
}


try {
    # Remove folders/files that we don't need any more
    Remove-Item .\7zip -Recurse

    Write-Output "INFO: Finished cleanup"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not remove items in final cleanup"
    Exit
}
