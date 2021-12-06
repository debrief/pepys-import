# Get the path to the network master install from the Pepys config file
# To make this as reliable as possible, we use Pepys own config parsing code
$network_path = python -c "import config; print(config.NETWORK_MASTER_INSTALL_PATH)"

if ($network_path -eq "") {
    Write-Output "Network path not set in config file, cannot copy."
    Exit 1
}



try {
    Write-Output "Deleting old version of Pepys"
    Set-Location -Path ..
    # Delete all except the bin directory, as that directory is still kept open by the Powershell/CMD process
    Remove-Item -Path * -Recurse -Force -Exclude bin -Verbose
    # Move to bin and delete all the contents, but not the folder (it's fine to keep the folder, as we're
    # always going to have a bin directory)
    Set-Location -Path bin
    Remove-Item -Path *
    # Change back to the main directory
    Set-Location -Path ..
    Write-Output "Copying new version of Pepys from $network_path"
    Copy-Item -Path "$network_path\*" -Destination "." -Recurse -Force -Verbose -Exclude ".git"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not copy new Pepys version"
    Exit 1
}

Write-Output "Copy completed"