If (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))
{
    # Relaunch as an elevated process:
    Start-Process powershell.exe "-File", ('"{0}"' -f $MyInvocation.MyCommand.Path) -Verb RunAs
    exit
}
function Install-Chocolatey
{
    try
    {
        if (-Not(Get-Command choco -ErrorAction SilentlyContinue))
        {
            Write-Host "Installing Chocolatey..."
            Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
        }
        else
        {
            Write-Host "Chocolatey is already installed."
        }
    }
    catch
    {
        Write-Host "Failed to install Chocolatey due to $_"
        Read-Host "Press any key to exit..."
        exit 1
    }
}

function Install-Git
{
    try
    {
        if (-Not(Get-Command git -ErrorAction SilentlyContinue))
        {
            Write-Host "Installing Git..."
            choco install git -y
        }
        else
        {
            Write-Host "Git is already installed."
        }
    }
    catch
    {
        Write-Host "Failed to install Git due to $_"
        Read-Host "Press any key to exit..."
        exit 1
    }
}

function Install-Python
{
    try
    {
        Write-Host "Installing Python..."
        choco install python --version=3.11.3 -y
    }
    catch
    {
        Write-Host "Failed to install Python due to $_"
        Read-Host "Press any key to exit..."
        exit 1
    }
}
try
{
    $scriptPath = Join-Path -Path $PSScriptRoot -ChildPath "test.ps1"
    Write-Host "Script Path: $scriptPath"
    if (Test-Path $scriptPath)
    {
        Start-Process powershell -ArgumentList "-File `"$scriptPath`" -Verb RunAs" -Wait
        Read-Host "First installation process completed, press enter to exit..."
        exit 0
    }
    Start-Process powershell -ArgumentList "-NoExit -File `"$scriptPath`" -Verb RunAs" -Wait
    Read-Host "Press Enter to exit"
}
catch
{
    Write-Host "Failed to install UpdateGuardian due to $_"
    Read-Host "Press Enter to exit"
    exit 1
}