# Make sure that scripts can run on the pc, if not, run the following command in powershell:
# Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser -confirm:$false -Force

# Check for pending reboot
function Test-PendingReboot
{
    $PendingRebootRegistryKeys = @(
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending',
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired',
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\PostRebootReporting',
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootInProgress'
    )

    foreach ($key in $PendingRebootRegistryKeys)
    {
        if (Test-Path -Path $key)
        {
            return $true
        }
    }

    try
    {
        $CBSRebootState = [System.Management.Automation.PSObject].Assembly.GetType('Microsoft.PowerShell.Commands.ManagementHelper')::CbsGetRebootState()
        if ($CBSRebootState)
        {
            return $true
        }
    }
    catch
    {
    }

    return $false
}

function Restart-ComputerAndRunScript
{
    $TaskName = "ssh_install_part2"
    $ScriptPath = $MyInvocation.MyCommand.Path
    $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File '$ScriptPath'"
    $Trigger = New-ScheduledTaskTrigger -AtStartup
    $Settings = New-ScheduledTaskSettingsSet -DontStopOnIdleEnd -RestartInterval (New-TimeSpan -Minutes 1) -RestartCount 3
    $Principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    $Task = New-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal
    $Task | Register-ScheduledTask -TaskName $TaskName

    # Reboot the computer
    Restart-Computer
}

# Function to check if a network adapter supports Wake-on-LAN
function Test-WoLSupport
{
    param (
        [string]$AdapterName
    )

    try
    {
        $PowerManagement = Get-PowerManagement -NetworkAdapterName $AdapterName -ErrorAction Stop
        return $PowerManagement.SupportsWakeOnMagicPacket
    }
    catch
    {
        return $false
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


# Check if OpenSSH feature is installed
$InstalledCapability = Get-WindowsCapability -Online -Name OpenSSH.Server* | Where-Object { $_.State -eq "Installed" }

if (-not$InstalledCapability)
{
    # Install OpenSSH feature if not already installed
    $Capability = Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 -ErrorAction SilentlyContinue
    if (-not$Capability)
    {
        Write-Host "Failed to install OpenSSH Server. Restart your computer and try running the script again." -ForegroundColor Red
        Read-Host "Press any key to stop the program"
        exit 1
    }
    else
    {
        Write-Host "OpenSSH Server installed successfully." -ForegroundColor Green
    }
    if (Test-PendingReboot)
    {
        Write-Host "A system restart is pending. Restart your computer to complete the installation." -ForegroundColor Yellow
        Write-Host "Please DO NOT make the script unavailable, or change its path before the reboot process." -ForegroundColor Red
        Read-Host "Press any key to continue and reboot"
        Restart-ComputerAndRunScript
    }
}
else
{
    Write-Host "OpenSSH Server is already installed." -ForegroundColor Yellow
}
$TaskName = "ssh_install_part2"

# Check if the scheduled task exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask)
{
    # If the task exists, remove it
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Scheduled task '$TaskName' has been removed." -ForegroundColor Green
}
else
{
    # If the task doesn't exist, do nothing
    Write-Host "Scheduled task '$TaskName' not found. No action taken." -ForegroundColor Yellow
}

# Check if sshd service exists
$SshdService = Get-Service sshd -ErrorAction SilentlyContinue
if (-not$SshdService)
{
    Write-Host "sshd service not found. Restart your computer to complete the installation of the OpenSSH server and run the script again." -ForegroundColor Yellow
    Read-Host "Press any key to stop the program"
    exit 1
}

# Start the sshd service
Start-Service sshd

# OPTIONAL but recommended:
Set-Service -Name sshd -StartupType 'Automatic'

# Confirm the Firewall rule is configured. It should be created automatically by setup. Run the following to verify
if (!(Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue | Select-Object Name, Enabled))
{
    Write-Output "Firewall Rule 'OpenSSH-Server-In-TCP' does not exist, creating it..."
    New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
}
else
{
    Write-Output "Firewall rule 'OpenSSH-Server-In-TCP' has been created and exists."
}
Write-Output ""

Write-Output "The OpenSSH Server has been installed and configured."

# Enable Wake on LAN for Ethernet adapters that support it
Get-NetAdapter | Where-Object { $_.Status -eq "Up" -and $_.InterfaceDescription -match "Ethernet" } | ForEach-Object {
    $AdapterName = $_.Name

    if (Test-WoLSupport -AdapterName $AdapterName)
    {
        Write-Host "Enabling Wake on LAN for adapter: $AdapterName"
        try
        {
            $PowerManagement = Get-PowerManagement -NetworkAdapterName $AdapterName -ErrorAction Stop
            if ($PowerManagement)
            {
                Set-PowerManagement -NetworkAdapterName $AdapterName -WakeOnMagicPacket $True -ErrorAction Stop
            }
        }
        catch
        {
            Write-Host "Failed to enable Wake on LAN for adapter: $AdapterName" -ForegroundColor Red
        }
    }
    else
    {
        Write-Host "Wake on LAN not supported by adapter: $AdapterName" -ForegroundColor Yellow
    }
}

$wolEnabled = $false

# Check for enabled Ethernet adapters with WoL support
Get-NetAdapter | Where-Object { $_.Status -eq "Up" -and $_.InterfaceDescription -match "Ethernet" } | ForEach-Object {
    $AdapterName = $_.Name
    if (Test-WoLSupport -AdapterName $AdapterName) {
        $wolEnabled = $true
    }
}

if (!$wolEnabled) {
    Write-Host "No enabled Ethernet adapters with Wake on LAN support found." -ForegroundColor Yellow
    Write-Host "If you have an Ethernet adapter that supports Wake on LAN, make sure it is enabled and run the script again." -ForegroundColor Yellow
    Read-Host "Press any key to stop the program"
    exit 1
}

# Wol firewall rule on remote PC on port 7 and 9 and on windows 10
$RuleName = "Wake-on-LAN"
$LocalPorts = "7,9"
$Protocol = "UDP"
$Profiles = "Domain,Private,Public"
$Action = "Allow"
$LocalIPAddress = "192.168.1.100" # Replace with the desired local IP address

# Check if the rule already exists
$ExistingRule = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue

if (-not$ExistingRule)
{
    # Create a new inbound rule for Wake-on-LAN
    $NewRule = New-NetFirewallRule -DisplayName $RuleName -Direction Inbound -Protocol $Protocol `
        -LocalPort $LocalPorts -Action $Action -Profile $Profiles.Split(",") `
        -Enabled True -Description "Rule for allowing Wake-on-LAN magic packets from a specific local IP address"
    Write-Host "Wake-on-LAN rule created successfully."

    # Set the rule to allow traffic only from the specified local IP address
    Set-NetFirewallRule -Name $NewRule.Name -RemoteAddress $LocalIPAddress
}
else
{
    Write-Host "Wake-on-LAN rule already exists."
}

Read-Host "Press any keys to end this installation process..."

