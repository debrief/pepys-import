$WshShell = New-Object -comObject WScript.Shell

$Shortcut = $WshShell.CreateShortcut(".\Pepys Import.lnk")
# We need to use full paths here or the shortcut will assume everything is relative to
# C:\
$Shortcut.TargetPath = [System.IO.Path]::GetFullPath(".\pepys_import.bat")
$Shortcut.IconLocation = [System.IO.Path]::GetFullPath(".\favicon.ico")
$Shortcut.Save()

$Shortcut = $WshShell.CreateShortcut(".\Pepys Import (persist).lnk")
$Shortcut.TargetPath = [System.IO.Path]::GetFullPath(".\pepys_import_persist.bat")
$Shortcut.IconLocation = [System.IO.Path]::GetFullPath(".\favicon.ico")
$Shortcut.Save()