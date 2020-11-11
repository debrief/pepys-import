# This script creates a standard user account and runs the specified program under
# that user account
# In this context, it is used to run pytest so that when the tests then run postgres.exe,
# postgres is running under a normal user rather than an admin user - as postgres
# refuses to start under an admin user
# 
# Part of the reason the code is so long is that we are streaming the stdout and stderr
# from the new process back into 
#
# This is an altered version of code from https://www.itdroplets.com/run-a-command-as-a-different-user-in-powershell/
# and https://stackoverflow.com/questions/23239127/powershell-stream-process-output-and-errors-while-running-external-process

# Definitions
$filename = "coverage.exe"
$arguments = 'run -m pytest -v --color=yes tests'

$username = 'pepys'
$password = 'cuKCr3gegNBrj4bP2USW'
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force

# Create a new user
New-LocalUser -Name $username -Password $securePassword

$credential = New-Object System.Management.Automation.PSCredential $username, $securePassword

$ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo

$ProcessInfo.FileName = $filename

$ProcessInfo.CreateNoWindow = $true
$ProcessInfo.RedirectStandardError = $true 
$ProcessInfo.RedirectStandardOutput = $true 
$ProcessInfo.UseShellExecute = $false

$ProcessInfo.Environment.Add("APPDATA", "C:\\Temp")

$ProcessInfo.Arguments = $arguments
$ProcessInfo.WorkingDirectory = $pwd

$ProcessInfo.Username = $Credential.GetNetworkCredential().username
$ProcessInfo.Domain = $Credential.GetNetworkCredential().Domain
$ProcessInfo.Password = $Credential.Password



#Finally start the process and wait for it to finish
$Process = New-Object System.Diagnostics.Process 
$Process.StartInfo = $ProcessInfo 


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

Exit $Process.ExitCode

# # $credential = New-Object System.Management.Automation.PSCredential ("username", (new-object System.Security.SecureString))
# $credential = New-Object System.Management.Automation.PSCredential $username, $securePassword
# # -ArgumentList "/c dir `"%systemdrive%\program files`""
# Start-Process -FilePath 'C:\Program Files\PostgreSQL\12\bin\postgres.exe' -Credential $credential -RedirectStandardOutput output.txt -RedirectStandardError error.txt -Wait
# type output.txt
# type error.txt
# dir output.txt
# dir error.txt

# Write-Output "Finished"