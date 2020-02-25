# There is no built-in way to create shortcuts in Powershell, so we use the old-fashioned
# Windows Scripting Host COM object
$WshShell = New-Object -comObject WScript.Shell

# On Windows icons are specified as a path, followed by a comma and a zero-based index into
# the icons inside the file (as, some files like DLLs can have multiple icons in them)
# As our .ico file has only one icon we just want index 0
$icon_path = [System.IO.Path]::GetFullPath(".\favicon.ico")
$icon_string = "$icon_path,0"

$Shortcut = $WshShell.CreateShortcut(".\Pepys Import.lnk")
# We need to use full paths here or the shortcut will assume everything is relative to
# C:\
$Shortcut.TargetPath = [System.IO.Path]::GetFullPath(".\pepys_import.bat")
$Shortcut.IconLocation = $icon_string
# If we don't set the working directory then we won't be able to import other DLLs or use relative paths
# to our Python executable
$Shortcut.WorkingDirectory = [System.IO.Path]::GetFullPath(".")
$Shortcut.Save()

$Shortcut = $WshShell.CreateShortcut(".\Pepys Import (persist).lnk")
$Shortcut.TargetPath = [System.IO.Path]::GetFullPath(".\pepys_import_persist.bat")
$Shortcut.IconLocation = $icon_string
$Shortcut.WorkingDirectory = [System.IO.Path]::GetFullPath(".")
$Shortcut.Save()