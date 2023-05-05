function Remove-DirectoryIfExists
{
    param (
        [string]$directoryPath
    )

    if (Test-Path -Path $directoryPath)
    {
        Remove-Item -Path $directoryPath -Recurse -Force
        Write-Host "Removed directory: $directoryPath"
    }
}


function Uninstall-OpenSSHServer
{
    try
    {
        $opensshServerFeature = Get-WindowsCapability -Name "OpenSSH.Server*" -Online

        if (-not$opensshServerFeature -or $opensshServerFeature.State -ne "Installed")
        {
            Write-Warning "OpenSSH server is not installed on this system."
            return
        }

        $programDataSSHPath = "C:\ProgramData\ssh"
        $currentUserSSHPath = Join-Path -Path (Resolve-Path "~") -ChildPath ".ssh"

        Remove-DirectoryIfExists -directoryPath $programDataSSHPath
        Remove-DirectoryIfExists -directoryPath $currentUserSSHPath

        Write-Host "Uninstalling OpenSSH server..."
        $uninstallResult = Remove-WindowsCapability -Name $opensshServerFeature.Name -Online

        if ($uninstallResult.RestartNeeded -eq "Yes")
        {
            Write-Host "Uninstallation completed. A restart is required to complete the process."
        }
        else
        {
            Write-Host "Uninstallation completed."
        }
    }
    catch
    {
        Write-Error "An error occurred while uninstalling OpenSSH server: $_"
        exit 1
    }
}

# Ensure the script is running with administrative privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator"))
{
    Write-Host "Running script without administrative privileges. Attempting to restart with admin rights..."
    $ScriptPath = $MyInvocation.MyCommand.Path
    $CurrentDirectory = (Get-Item -Path ".\").FullName
    Read-Host "Press Enter to continue, and re-run the script with administratives privileges."
    $AdminProcess = Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" -Verb RunAs -PassThru -WorkingDirectory $CurrentDirectory
    $AdminProcess.WaitForExit()
    $ExitCode = $AdminProcess.ExitCode
    exit $ExitCode
}
else
{
    Write-Host "Script is running with administrative privileges."
}

# Ensure the script is running with admin privileges
if (-not ([System.Security.Principal.WindowsPrincipal][System.Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator))
{
    Write-Error "This script must be run as an administrator."
    Read-Host "Press Enter to continue..."
    exit 1
}


if (-not ([System.Security.Principal.WindowsPrincipal][System.Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator))
{
    Write-Error "This script must be run as an administrator."
    Read-Host "Press Enter to continue..."
    exit 1
}

Uninstall-OpenSSHServer



Uninstall-OpenSSHServer
Read-Host "Press Enter to close the script..."
