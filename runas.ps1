$filename = "python.exe"
$arguments = "-m pytest tests/test_data_store_initialise.py::DataStoreInitialisePostGISTestCase -v -s"

# $filename = "python.exe"
# $arguments = "-c `"import os; print(os.environ['APPDATA'])`""

$username = 'pepys'
$password = 'cuKCr3gegNBrj4bP2USW'
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
New-LocalUser -Name $username -Password $securePassword

# $credential = New-Object System.Management.Automation.PSCredential ("username", (new-object System.Security.SecureString))
$credential = New-Object System.Management.Automation.PSCredential $username, $securePassword

#Use System.Diagnostics to start the process as UserB
$ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
#With FileName we're basically telling powershell to run another powershell process
$ProcessInfo.FileName = $filename
#CreateNoWindow helps avoiding a second window to appear whilst the process runs
$ProcessInfo.CreateNoWindow = $true
$ProcessInfo.RedirectStandardError = $true 
$ProcessInfo.RedirectStandardOutput = $true 
$ProcessInfo.UseShellExecute = $false

$ProcessInfo.Environment.Add("APPDATA", "C:\\Temp")

$ProcessInfo.Arguments = $arguments
#The next 3 lines are the credential for UserB, as you can see, we can't just pass $Credential
$ProcessInfo.Username = $Credential.GetNetworkCredential().username
$ProcessInfo.Domain = $Credential.GetNetworkCredential().Domain
$ProcessInfo.Password = $Credential.Password
$ProcessInfo.WorkingDirectory = $pwd
#Finally start the process and wait for it to finish
$Process = New-Object System.Diagnostics.Process 
$Process.StartInfo = $ProcessInfo 
# -ArgumentList "/c dir `"%systemdrive%\program files`""
# -RedirectStandardOutput output.txt -RedirectStandardError error.txt -Wait
# $process = Start-Process -PassThru -FilePath 'python.exe' -ArgumentList "count.py" -Credential $credential -RedirectStandardError "error.txt" -RedirectStandardOutput "output.txt"

# Register Object Events for stdin\stdout reading
$OutEvent = Register-ObjectEvent -Action {
    Write-Host $Event.SourceEventArgs.Data
} -InputObject $Process -EventName OutputDataReceived

$ErrEvent = Register-ObjectEvent -Action {
    Write-Host $Event.SourceEventArgs.Data
} -InputObject $Process -EventName ErrorDataReceived

$Process.Start() | Out-Null

$Process.BeginOutputReadLine()
$Process.BeginErrorReadLine()

do
{
    Start-Sleep -Seconds 1
}
while (!$Process.HasExited)

$OutEvent.Name, $ErrEvent.Name |
    ForEach-Object {Unregister-Event -SourceIdentifier $_}

Write-Output "Finished"

# # $credential = New-Object System.Management.Automation.PSCredential ("username", (new-object System.Security.SecureString))
# $credential = New-Object System.Management.Automation.PSCredential $username, $securePassword
# # -ArgumentList "/c dir `"%systemdrive%\program files`""
# Start-Process -FilePath 'C:\Program Files\PostgreSQL\12\bin\postgres.exe' -Credential $credential -RedirectStandardOutput output.txt -RedirectStandardError error.txt -Wait
# type output.txt
# type error.txt
# dir output.txt
# dir error.txt

# Write-Output "Finished"