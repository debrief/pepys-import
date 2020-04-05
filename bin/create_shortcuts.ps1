# There is no built-in way to create shortcuts in Powershell, so we use the old-fashioned
# Windows Scripting Host COM object
$WshShell = New-Object -comObject WScript.Shell

#
# Add shortcuts to Send To folder
#

# Get the User's Send To folder location
# This is safer than using a hard-coded PATH as network/user settings may mean the folder
# is in an unexpected place
$sendto_location = $WshShell.SpecialFolders("SendTo")

# On Windows icons are specified as a path, followed by a comma and a zero-based index into
# the icons inside the file (as, some files like DLLs can have multiple icons in them)
# As our .ico file has only one icon we just want index 0
$icon_path = [System.IO.Path]::GetFullPath(".\favicon.ico")
$icon_string = "$icon_path,0"

#
# Add Pepys Import shortcut to Send To
#

$shortcut_loc = $sendto_location + "\Pepys Import.lnk"

if (Test-Path $shortcut_loc) { Remove-Item $shortcut_loc; }

$Shortcut = $WshShell.CreateShortcut($shortcut_loc)
# We need to use full paths here or the shortcut will assume everything is relative to
# C:\
$Shortcut.TargetPath = [System.IO.Path]::GetFullPath(".\pepys_import.bat")
$Shortcut.IconLocation = $icon_string
# If we don't set the working directory then we won't be able to import other DLLs or use relative paths
# to our Python executable
$Shortcut.WorkingDirectory = [System.IO.Path]::GetFullPath(".")
$Shortcut.Save()


#
# Add Pepys Import (no archive) shortcut to Send To
#

$shortcut_loc = $sendto_location + "\Pepys Import (no archive).lnk"

if (Test-Path $shortcut_loc) { Remove-Item $shortcut_loc; }

$Shortcut = $WshShell.CreateShortcut($shortcut_loc)
$Shortcut.TargetPath = [System.IO.Path]::GetFullPath(".\pepys_import_no_archive.bat")
$Shortcut.IconLocation = $icon_string
$Shortcut.WorkingDirectory = [System.IO.Path]::GetFullPath(".")
$Shortcut.Save()

#
# Add shortcut to Start Menu
#

# Get the User's Start Menu folder
$startmenu_location = "$env:USERPROFILE\Start Menu\Programs\"

# Delete Pepys folder in Start Menu if it exists
$pepys_folder = $startmenu_location + "\Pepys"

if (Test-Path $pepys_folder) { Remove-Item $pepys_folder -Recurse ; }

# Create Pepys folder in Start Menu
New-Item -Path $startmenu_location -Name "Pepys" -ItemType "directory"

$Shortcut = $WshShell.CreateShortcut($startmenu_location + "Pepys\Pepys Admin.lnk")
$Shortcut.TargetPath = [System.IO.Path]::GetFullPath(".\pepys_admin.bat")
$Shortcut.IconLocation = $icon_string
$Shortcut.WorkingDirectory = [System.IO.Path]::GetFullPath(".")
$Shortcut.Save()