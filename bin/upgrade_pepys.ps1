$network_path = python -c "import config; print(config.NETWORK_MASTER_INSTALL_PATH)"

Write-Output "Copying new version of Pepys from $network_path"

try {
    Copy-Item -Path $network_path -Destination "..\" -Recurse
}
catch {
    Write-Output $_
    Write-Output "ERROR: Could not copy new Pepys version"
    Exit 1
}

Write-Output "Copy completed"