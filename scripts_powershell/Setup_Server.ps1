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

function Clone-Repository
{
    try
    {
        $repoUrl = "https://github.com/flintpop/updateguardian"
        $destinationPath = "$env:USERPROFILE\UpdateGuardian"
        if (-Not(Test-Path -Path $destinationPath))
        {
            Write-Host "Cloning repository..."
            git clone $repoUrl $destinationPath
        }
        else
        {
            Write-Host "Repository is already cloned"
        }
    }
    catch
    {
        Write-Host "Failed to clone repository due to $_"
        Read-Host "Press any key to exit..."
        exit 1
    }
}

function Install-Python-Dependencies
{
    try
    {
        Write-Host "Upgrading pip..."
        python.exe -m pip install --upgrade pip
        Write-Host "Installing Python dependencies..."
        $destinationPath = "$env:USERPROFILE\UpdateGuardian"
        pip install -r "$destinationPath\requirements.txt"
    }
    catch
    {
        Write-Host "Failed to install Python dependencies due to $_"
        Read-Host "Press any key to exit..."
        exit 1
    }
}


function Start-UpdateGuardian
{
    try
    {
        Write-Host "Starting UpdateGuardian..."
        $destinationPath = "$env:USERPROFILE\UpdateGuardian"
        python "$destinationPath\src\server\main.py"
    }
    catch
    {
        Write-Host "Failed to start UpdateGuardian due to $_"
        Read-Host "Press any key to exit..."
        exit 1
    }
}

try
{
    Install-Chocolatey
    Install-Git
    Install-Python

    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

    Clone-Repository
    Install-Python-Dependencies
    Start-UpdateGuardian
    Read-Host "Press Enter to exit"
    exit 0
}
catch
{
    Write-Host "Failed to install UpdateGuardian due to $_"
    Read-Host "Press Enter to exit"
    exit 1
}