# Make sure that scripts can run on the pc, if not, run the following command in powershell:
# Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser -confirm:$false -Force

# Ensure the script is running with administrative privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator"))
{
    Start-Process powershell.exe "-File",('"{0}"' -f $MyInvocation.MyCommand.Path) -Verb RunAs
    exit
}

# Enable OpenSSH feature
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

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

# Wol firewall rule on remote PC on port 7 and 9 and on windows 10
$RuleName = "Wake-on-LAN"
$LocalPorts = "7,9"
$Protocol = "UDP"
$Profiles = "Domain,Private,Public"
$Action = "Allow"
$LocalIPAddress = "192.168.1.100" # Replace with the desired local IP address

# Check if the rule already exists
$ExistingRule = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue

if (-not $ExistingRule) {
    # Create a new inbound rule for Wake-on-LAN
    $NewRule = New-NetFirewallRule -DisplayName $RuleName -Direction Inbound -Protocol $Protocol `
        -LocalPort $LocalPorts -Action $Action -Profile $Profiles.Split(",") `
        -Enabled True -Description "Rule for allowing Wake-on-LAN magic packets from a specific local IP address"
    Write-Host "Wake-on-LAN rule created successfully."

    # Set the rule to allow traffic only from the specified local IP address
    Set-NetFirewallRule -Name $NewRule.Name -RemoteAddress $LocalIPAddress
} else {
    Write-Host "Wake-on-LAN rule already exists."
}

Read-Host "Press any keys to close this window..."
