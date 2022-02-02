Function Make-Shortcut($ShortcutLocation, $TargetPath, $Icon)
{
    if (Test-Path $ShortcutLocation) { Remove-Item $ShortcutLocation; }

    $Shortcut = $WshShell.CreateShortcut($ShortcutLocation)
    # We need to use full paths here or the shortcut will assume everything is relative to
    # C:\
    $Shortcut.TargetPath = [System.IO.Path]::GetFullPath($TargetPath)
    $Shortcut.IconLocation = $Icon
    # If we don't set the working directory then we won't be able to import other DLLs or use relative paths
    # to our Python executable
    $Shortcut.WorkingDirectory = [System.IO.Path]::GetFullPath(".")
    $Shortcut.Save()
}

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
try {
    Make-Shortcut -ShortcutLocation ($sendto_location + "\Pepys Import.lnk") -TargetPath ".\pepys_import_sendto.bat" -Icon $icon_string
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not create Pepys Import Send-To Shortcut"
    Exit 1
}



#
# Add Pepys Import (no archive) shortcut to Send To
#
try {
    Make-Shortcut -ShortcutLocation ($sendto_location + "\Pepys Import (no archive).lnk") -TargetPath ".\pepys_import_no_archive_sendto.bat" -Icon $icon_string
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not create Pepys Import (no archive) Send-To Shortcut"
    Exit 1
}

#
# Add Pepys Import (training mode) shortcut to Send To
#
try {
    Make-Shortcut -ShortcutLocation ($sendto_location + "\Pepys Import (training mode).lnk") -TargetPath ".\pepys_import_training_sendto.bat" -Icon $icon_string
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not create Pepys Import (training mode) Send-To Shortcut"
    Exit 1
}

#
# Add shortcuts to Start Menu
#
try {
    # Get the User's Start Menu folder
    $startmenu_location = "$env:USERPROFILE\Start Menu\Programs\"

    # Delete Pepys folder in Start Menu if it exists
    $pepys_folder = $startmenu_location + "\Pepys"

    if (Test-Path $pepys_folder) { Remove-Item $pepys_folder -Recurse ; }

    # Create Pepys folder in Start Menu
    New-Item -Path $startmenu_location -Name "Pepys" -ItemType "directory"

    # Pepys Admin shortcuts
    Make-Shortcut -ShortcutLocation ($startmenu_location + "Pepys\Pepys Admin.lnk") -TargetPath ".\pepys_admin.bat" -Icon $icon_string
    Make-Shortcut -ShortcutLocation ($startmenu_location + "Pepys\Pepys Admin (training mode).lnk") -TargetPath ".\pepys_admin_training.bat" -Icon $icon_string
    
    # Pepys Viewer shortcuts
    Make-Shortcut -ShortcutLocation ($startmenu_location + "Pepys\Pepys Viewer.lnk") -TargetPath ".\pepys_viewer.bat" -Icon $icon_string
    Make-Shortcut -ShortcutLocation ($startmenu_location + "Pepys\Pepys Viewer (training mode).lnk") -TargetPath ".\pepys_viewer_training.bat" -Icon $icon_string

    Make-Shortcut -ShortcutLocation ($startmenu_location + "Pepys\Upgrade Pepys.lnk") -TargetPath ".\upgrade_pepys.bat" -Icon $icon_string
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not create Pepys Admin Start Menu shortcuts"
    Exit 1
}


#
# Add Pepys bin folder to User's PATH variable
#
try {
    $pepys_bin_path = [System.IO.Path]::GetFullPath(".")

    if (!($env:Path -split ';' -contains $pepys_bin_path)) {
        [Environment]::SetEnvironmentVariable(
            "PATH",
            $pepys_bin_path + ";" + [Environment]::GetEnvironmentVariable("PATH", [EnvironmentVariableTarget]::User),
            [EnvironmentVariableTarget]::User)
    }
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not add Pepys bin folder to user's PATH"
    Exit 1
}


try {
    # Create file associations for .sqlite and .db files to open in Pepys Admin
    $pepys_admin_run_command = [System.IO.Path]::GetFullPath(".\pepys_admin.bat") + " --db %1"

    # All of the assigning to $null below is just to stop the default output showing exactly
    # what registry keys have been created

    # Create the file extension entry for .sqlite and assign it to the filetype sqlitefile
    $null = New-Item -Path HKCU:\Software\Classes -Name .sqlite -Value sqlitefile -Force
    # Do the same for the .db extension
    $null = New-Item -Path HKCU:\Software\Classes -Name .db -Value sqlitefile -Force
    # Specify the 'shell open' command for the filetype sqlitefile (that both extensions reference)
    $null = New-Item -Path HKCU:\Software\Classes\sqlitefile\shell\open -Force -Name command -Value "$pepys_admin_run_command"
    # Set the default icon for the filetype to the Pepys icon
    $null = New-Item -Path HKCU:\Software\Classes\sqlitefile -Force -Name DefaultIcon -Value $icon_string
    # Refresh the Windows Explorer icon cache, so the icons show immediately
    ie4uinit.exe -show
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not create file assocations"
    Exit 1
}


# Copy tutorial files into folder in user's home directory
try {
    New-Item -Path $env:USERPROFILE -Name "Pepys_Training_Data" -ItemType "directory" -Force
    Copy-Item -Path "..\tutorial" -Destination "$env:USERPROFILE\Pepys_Training_Data" -Recurse -Force
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not copy tutorial data to home folder"
    Exit 1
}
