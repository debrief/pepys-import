Write-Output "INFO: Starting to create Pepys deployment"

# Download embedded Python distribution
$url = 'https://www.python.org/ftp/python/3.7.6/python-3.7.6-embed-amd64.zip'
(New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\python.zip")

# Extract zip file
Expand-Archive -Path python.zip -DestinationPath .\python -Force
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
$url = 'http://www.gaia-gis.it/gaia-sins/windows-bin-amd64/spatialite-loadable-modules-5.0.0-win-amd64.7z'
(New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\spatialite-loadable-modules-5.0.0-win-amd64.7z")

# mod_spatialite comes in a 7zip archive, so we need to download 7zip to be able to extract it
$url = 'http://www.7-zip.org/a/7za920.zip'
(New-Object System.Net.WebClient).DownloadFile($url,  "$PWD\7zip.zip")
# Put the 7zip exe in the .\7zip folder - we will delete this later
Expand-Archive -Path 7zip.zip -DestinationPath .\7zip -Force

# Extract the mod_spatialite 7zip file into the lib folder (it creates its own subfolder in there)
.\7zip\7za.exe x .\spatialite-loadable-modules-5.0.0-win-amd64.7z -olib -y

if ($LastExitCode -ne 0)
{
    Write-Output "ERROR: Could not extract spatialite file - has the URL broken?"
    exit
}

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
import site
"@

Set-Content -Encoding ascii .\python\Lib\site-packages\extra_paths.pth @"
import sys; sys.path.insert(0, "")
pip\_vendor\pep517
"@


Write-Output "INFO: Set Python pth files"

# Do a standard pip install of the requirements and dev requirements, not warning us that scripts will be unavailable
.\python\python.exe -m pip install -r requirements.txt -r requirements_dev.txt --no-warn-script-location --no-cache-dir

Write-Output "INFO: Installed Python dependencies"

Remove-Item *.zip
Remove-Item *.7z
Remove-Item get-pip.py

Write-Output "INFO: Cleaned up all except 7zip"

Write-Output "INFO: Building documentation"
# Write to the same folder that 'make html' does, so it works for devs who've done that on other platforms
.\python\Scripts\sphinx-build.exe docs docs\_build\html

write-Output "INFO: Finished building documentation"

# Zip up whole folder into a zip-file with the current date in the filename
# excluding the 7zip folder
$date_str = Get-Date -Format "yyyyMMdd"
$output_filename = $date_str + "_pepys-import.zip"
.\7zip\7za.exe a .\$output_filename .\* -xr!7zip/ -xr!"bin\distlib-0.3.0-py2.py3-none-any.whl"

Write-Output "INFO: Written zipped deployment file to $output_filename"

# Remove folders/files that we don't need any more
Remove-Item .\7zip -Recurse

Write-Output "INFO: Finished cleanup"