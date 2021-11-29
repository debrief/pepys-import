# Get the path to the network master install from the Pepys config file
# To make this as reliable as possible, we use Pepys own config parsing code
$network_path = python -c "import config; print(config.NETWORK_MASTER_INSTALL_PATH)"

if ($network_path -eq "") {
    Write-Output "Network path not set in config file, cannot copy."
    Exit 1
}

Write-Output "Copying new version of Pepys from $network_path"

try {
    Copy-Item -Path "$network_path\*" -Destination "..\" -Recurse -Force -Verbose -Exclude ".git"
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not copy new Pepys version"
    Exit 1
}

Write-Output "Copy completed"