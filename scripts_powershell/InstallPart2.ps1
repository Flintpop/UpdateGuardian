If (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))
{
    # Relaunch as an elevated process:
    Start-Process powershell.exe "-File", ('"{0}"' -f $MyInvocation.MyCommand.Path) -Verb RunAs
    exit
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
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    Clone-Repository
    Install-Python-Dependencies
    Start-UpdateGuardian
    Write-Host "It worked"
    Read-Host "Press Enter to exit"
}
catch
{
    Write-Host "It failed"
    Read-Host "Press Enter to exit"
}