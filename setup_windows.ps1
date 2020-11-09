# Create lib folder
New-Item -Path "." -Name "lib" -ItemType "directory"

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
    # Extract SQLite DLL to a lib/sqlite-python folder
    Expand-Archive -Path sqlite.zip -DestinationPath .\lib\sqlite-python -Force
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
    .\7zip\7za.exe x .\spatialite-loadable-modules-5.0.0-win-amd64.7z -olib\ -y

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
    # Download PostGIS install
    $url = 'http://download.osgeo.org/postgis/windows/pg12/postgis-bundle-pg12-3.0.2x64.zip'
    (New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\postgis.zip")
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not download PostGIS - has the URL changed?"
    Exit
}

try {
    # Extract PostGIS zip into the Postgres installation folder
    Expand-Archive -Path postgis.zip -DestinationPath  "c:\Program Files\PostgreSQL\12" -Force
    Write-Output "INFO: Downloaded and extracted PostGIS"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not extract PostGIS zip file"
    Exit
}

# Get the DLLs folder for the Python install being used
# (We can't hard-code this as we may get different point release versions)
$DLL = python get_DLL.py | Out-String
Copy-Item $DLL.Trim() -Destination ".\lib\sqlite-python"

Write-Output "INFO: Copied SQLite pyd file"