# Get the User's Send To folder location
# This is safer than using a hard-coded PATH as network/user settings may mean the folder
# is in an unexpected place
$WshShell = New-Object -comObject WScript.Shell
$sendto_location = $WshShell.SpecialFolders("SendTo")

Copy-Item ".\Pepys Import.lnk" $sendto_location
Copy-Item ".\Pepys Import (persist).lnk" $sendto_location

Write-Output "Copied all Pepys shortcuts to Send To folder at $sendto_location"