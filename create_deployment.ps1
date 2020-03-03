Write-Output "INFO: Starting to create Pepys deployment"

# Download embedded Python distribution
$url = 'https://www.python.org/ftp/python/3.7.6/python-3.7.6-embed-amd64.zip'
(New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\python.zip")

# Extract zip file
Expand-Archive -Path python.zip -DestinationPath .\python
Write-Output "INFO: Downloaded and extracted embedded Python"

# Download and run get-pip to install pip
$url = 'https://bootstrap.pypa.io/get-pip.py'
(New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\get-pip.py")

.\python\python.exe .\get-pip.py --no-warn-script-location

Write-Output "INFO: Installed pip"

# Download SQLite DLL
$url = 'https://www.sqlite.org/2020/sqlite-dll-win64-x64-3310100.zip'
(New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\sqlite.zip")

# Extract SQLite DLL to Python folder, deliberately overwriting sqlite3.dll provided by Python
# (note the -Force argument, to force overwriting)
Expand-Archive -Path sqlite.zip -DestinationPath .\python -Force

Write-Output "INFO: Downloaded and extracted SQLite"

# Download mod_spatialite DLL files
$url = 'http://www.gaia-gis.it/gaia-sins/windows-bin-NEXTGEN-amd64/mod_spatialite-NG-win-amd64.7z'
(New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\mod_spatialite.7z")

# mod_spatialite comes in a 7zip archive, so we need to download 7zip to be able to extract it
$url = 'http://www.7-zip.org/a/7za920.zip'
(New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\7zip.zip")
# Put the 7zip exe in the .\7zip folder - we will delete this later
Expand-Archive -Path 7zip.zip -DestinationPath .\7zip

# Extract the mod_spatialite 7zip file into the lib folder (it creates its own subfolder in there)
.\7zip\7za.exe x .\mod_spatialite.7z -olib

Write-Output "INFO: Downloaded and extracted mod_spatialite"

# Set the Python Path file to tell it where to find modules - including the new pip location and
# the directory above the python folder (with pepys-import in it). This creates a ._pth file which
# Python uses as it's *only* source for generating sys.path (ie. it does NOT take into account
# environment variables such as PYTHONPATH)
Set-Content -Encoding ascii .\python\python37._pth @"
python37.zip
.
Lib\site-packages
..
"@

Write-Output "INFO: Set Python pth file"

# Do a standard pip install of the requirements, not warning us that scripts will be unavailable
.\python\python.exe -m pip install -r requirements.txt --no-warn-script-location

Write-Output "INFO: Installed Python dependencies"

# Remove folders/files that we don't need any more
Remove-Item .\7zip -Recurse
Remove-Item *.zip
Remove-Item *.7z
Remove-Item get-pip.py

Write-Output "INFO: Finished cleanup"

# Zip up whole folder into a zip-file with the current date in the filename
$date_str = Get-Date -Format "yyyymmdd"
$output_filename = $date_str + "_pepys-import.zip"
Compress-Archive -Path .\* -DestinationPath $output_filename

Write-Output "INFO: Written zipped deployment file to $output_filename"