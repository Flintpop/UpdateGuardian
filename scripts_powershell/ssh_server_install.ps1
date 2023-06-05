# Make sure that scripts can run on the pc, if not, run the following command in powershell:
# Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser -confirm:$false -Force

function Check-AndCreateICMPRule
{
    $RuleName = "Allow_ICMP"
    $RuleExists = $false

    try
    {
        $ExistingRules = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction Stop
        if ($ExistingRules)
        {
            $RuleExists = $true
            Write-Host "Firewall rule '$RuleName' already exists."
        }
    }
    catch
    {
        if ($_.Exception -is [System.Management.Automation.ActionPreferenceStopException])
        {
            Write-Host "Error occurred while checking the firewall rule: $( $_.Exception.InnerException.Message )"
        }
    }

    if (-not$RuleExists)
    {
        try
        {
            New-NetFirewallRule -DisplayName $RuleName -Direction Inbound -Action Allow -Protocol ICMPv4 -ErrorAction Stop
            Write-Host "Firewall rule '$RuleName' has been created."
        }
        catch
        {
            Write-Host "Error occurred while creating the firewall rule: $( $_.Exception.Message )"
        }
    }
}

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

function Get-InternetConnectedAdapterMacAddress
{
    try
    {
        $connectedAdapters = Get-NetAdapter -Physical -ErrorAction Stop | Where-Object { $_.Status -eq 'Up' }

        if ($connectedAdapters -eq $null)
        {
            Write-Host "No physical network adapters with 'Up' status were found."
            return $null
        }

        $internetConnectedAdapter = $null
        foreach ($adapter in $connectedAdapters)
        {
            $ipConfiguration = Get-NetIPConfiguration -InterfaceIndex $adapter.InterfaceIndex
            if ($ipConfiguration.IPv4DefaultGateway -ne $null)
            {
                $internetConnectedAdapter = $adapter
                break
            }
        }

        if ($internetConnectedAdapter -eq $null)
        {
            Write-Host "No network adapters with an IPv4 default gateway were found."
            return $null
        }

        $macAddress = $internetConnectedAdapter.MacAddress
        return $macAddress
    }
    catch
    {
        Write-Host "An error occurred while executing the function: $( $_.Exception.Message )"
        return $null
    }
}

function Test-IsPublicKeyValid($publicKey)
{
    if ($null -eq $publicKey -or $publicKey -eq "")
    {
        return $false
    }

    #    $keyParts = $publicKey -split '\s+'
    #    if ($keyParts.Count -lt 2 -or $keyParts[0] -notmatch "^ssh-(rsa|dss|ed25519)") {
    #        return $false
    #    }

    return $true
}


function Configure-OpenSSHServer
{
    $sshdConfigPath = "C:\ProgramData\ssh\sshd_config"

    # Check if the file exists
    if (-not(Test-Path -Path $sshdConfigPath))
    {
        Write-Error "The sshd_config file does not exist at the specified path: $sshdConfigPath"
        Read-Host -Prompt "Press Enter to exit"
        exit 1
    }

    # Read the file content into a variable
    $sshdConfig = Get-Content -Path $sshdConfigPath -ErrorAction Stop

    # Modify the content
    $modifiedSshdConfig = $sshdConfig -replace '#PubkeyAuthentication yes', 'PubkeyAuthentication yes' -replace '#PasswordAuthentication yes', 'PasswordAuthentication no'

    # Match "Match Group administrators" block and comment it out
    $inAdminGroupBlock = $false
    for ($i = 0; $i -lt $modifiedSshdConfig.Count; $i++) {
        if ($modifiedSshdConfig[$i] -match 'Match Group administrators')
        {
            $inAdminGroupBlock = $true
        }
        if ($inAdminGroupBlock -and -not($modifiedSshdConfig[$i] -match '^#'))
        {
            $modifiedSshdConfig[$i] = "# " + $modifiedSshdConfig[$i]
        }
        if ($modifiedSshdConfig[$i] -match '^#\s+AuthorizedKeysFile')
        {
            $inAdminGroupBlock = $false
        }
    }

    # Write the modified content back to the file
    try
    {
        Set-Content -Path $sshdConfigPath -Value $modifiedSshdConfig -ErrorAction Stop
        Write-Host "The sshd_config file has been successfully modified."
    }
    catch
    {
        Write-Error "An error occurred while writing the modified content to the sshd_config file: $_"
        exit 1
    }
    $currentShell = Get-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell | Select-Object -ExpandProperty DefaultShell

    # Check if the current shell is not cmd
    if ($currentShell -ne "C:\Windows\System32\cmd.exe")
    {
        # Change the default shell to cmd
        Set-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value "C:\Windows\System32\cmd.exe"
        Write-Output "Default SSH server shell has been changed to cmd."
    }
    else
    {
        Write-Output "Default SSH server shell is already cmd."
    }
    Write-Output ""
}

function Set-RightsSSHServerFiles
{
    try
    {
        $homeDir = [System.Environment]::GetFolderPath('UserProfile')
        $authorizedKeysPath = Join-Path -Path $homeDir -ChildPath ".ssh\authorized_keys"
        $sshFolderPath = Join-Path -Path $homeDir -ChildPath ".ssh"

        if (-not(Test-Path -Path $sshFolderPath))
        {
            try
            {
                New-Item -ItemType Directory -Path $sshFolderPath -ErrorAction Stop
                Write-Host "Created .ssh folder at the specified path: $sshFolderPath"
            }
            catch
            {
                Write-Error "Failed to create the .ssh folder at the specified path: $sshFolderPath"
                Read-Host "Press enter to stop the program"
                exit 1
            }
        }

        if (-not(Test-Path -Path $authorizedKeysPath))
        {
            try
            {
                New-Item -ItemType File -Path $authorizedKeysPath -ErrorAction Stop
                Write-Host "Created authorized_keys file at the specified path: $authorizedKeysPath"
            }
            catch
            {
                Write-Error "Failed to create the authorized_keys file at the specified path: $authorizedKeysPath"
                Read-Host "Press enter to stop the program"
                exit 1
            }
        }

        Write-Host "Setting permissions for the .ssh folder..."
        $sshFolderAcl = Get-Acl -Path $sshFolderPath
        $sshFolderAcl.SetAccessRuleProtection($true, $false)
        $sshFolderRights = [System.Security.AccessControl.FileSystemRights]::FullControl
        $inheritanceFlags = [System.Security.AccessControl.InheritanceFlags]::None
        $propagationFlags = [System.Security.AccessControl.PropagationFlags]::None
        $allowance = [System.Security.AccessControl.AccessControlType]::Allow

        $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
        $sshFolderAcl.SetAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($currentUser, $sshFolderRights, $inheritanceFlags, $propagationFlags, $allowance)))
        $sshFolderAcl.SetAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule("SYSTEM", $sshFolderRights, $inheritanceFlags, $propagationFlags, $allowance)))
        Set-Acl -Path $sshFolderPath -AclObject $sshFolderAcl

        Write-Host "Setting permissions for the authorized_keys file..."
        $authorizedKeysAcl = Get-Acl -Path $authorizedKeysPath
        $authorizedKeysAcl.SetAccessRuleProtection($true, $false)

        $authorizedKeysAcl.SetAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($currentUser, $sshFolderRights, $inheritanceFlags, $propagationFlags, $allowance)))
        $authorizedKeysAcl.SetAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule("SYSTEM", $sshFolderRights, $inheritanceFlags, $propagationFlags, $allowance)))
        Set-Acl -Path $authorizedKeysPath -AclObject $authorizedKeysAcl

        Write-Host "Permissions have been set successfully."
    }
    catch
    {
        Write-Error "An error occurred while setting permissions: $_"
        exit 1
    }
}

Write-Host ""
$server_ip = "192.168.2.80"


# Ensure the script is running with administrative privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator"))
{
    $ScriptPath = $MyInvocation.MyCommand.Path
    $CurrentDirectory = (Get-Item -Path ".\").FullName
    $AdminProcess = Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" -Verb RunAs -PassThru -WorkingDirectory $CurrentDirectory
    exit 0
}
else
{
    Write-Host "Script is running with administrative privileges."
}


# Check if rules for ping command are configured
Write-Host "Checking if ICMP rules are configured..."
Check-AndCreateICMPRule
Write-Host "ICMP rules are configured."
Write-Host ""

# Check if OpenSSH feature is installed
$InstalledCapability = Get-WindowsCapability -Online -Name OpenSSH.Server* | Where-Object { $_.State -eq "Installed" }

if (-not$InstalledCapability)
{
    # Install OpenSSH feature
    Write-Host "Installing OpenSSH Server..."
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
        Read-Host "Press any key to continue and reboot"
        Restart-Computer
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

# Check if shd service exists
$SshdService = Get-Service sshd -ErrorAction SilentlyContinue
if (-not$SshdService)
{
    Write-Host "sshd service not found. Restart your computer to complete the installation of the OpenSSH server and run the script again." -ForegroundColor Yellow
    Write-Host "There may be a problem installing the service. If the problem persists, try running the script again." -ForegroundColor Red
    Read-Host "Press any key to stop the program"
    exit 1
}


# Start the sshd service
Write-Host ""
Write-Host "Starting for the first time the sshd service..."
Start-Service sshd

Write-Host "Stopping the sshd service..."
Stop-Service sshd

Write-Host ""
Write-Host "Configuring OpenSSH Server..."
Configure-OpenSSHServer
Write-Host ""
Write-Host "OpenSSH Server has been configured successfully." -ForegroundColor Green
Write-Host "Setting up the corrects rights for pubkey ssh authentification..."
Write-Host ""
Set-RightsSSHServerFiles
Write-Host ""

Write-Host "Restarting the sshd service..."
Start-Service sshd

Write-Host ""
# Start the service at each boot
Write-Host "Setting the sshd service to start automatically at each boot..."
Set-Service -Name sshd -StartupType 'Automatic'
Write-Host ""

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
Write-Host ""

# Get the computer name
$computer_name = $env:COMPUTERNAME

try
{
    $defaultGatewayAdapter = Get-NetRoute -DestinationPrefix 0.0.0.0/0 | Where-Object { $_.NextHop -ne "::" } | Get-NetIPInterface | Get-NetAdapter -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Up' }

    if ($null -eq $defaultGatewayAdapter)
    {
        Write-Host "No network adapter is up and running." -ForegroundColor Red
        Read-Host "Press any key to stop the program"
        exit 1
    }
    Write-Host "Using network adapter '$( $defaultGatewayAdapter.Name )' to retrieve local ipv4 address..."
    $ipv4_address = (Get-NetIPAddress -InterfaceIndex $defaultGatewayAdapter.ifIndex -AddressFamily IPv4 -PrefixOrigin Dhcp).IPAddress
    if ($null -eq $ipv4_address)
    {
        Write-Host "No IPv4 address found." -ForegroundColor Red
        Read-Host "Press any key to stop the program"
        exit 1
    }

    Write-Host "Local IPv4 address found: $ipv4_address" -ForegroundColor Green
    Write-Host "Retreiving MAC address of the internet-connected adapter..."
    $mac = Get-InternetConnectedAdapterMacAddress
    if ($null -eq $mac)
    {
        Write-Host "No MAC address found for the internet-connected adapter." -ForegroundColor Red
        Read-Host "Press any key to stop the program"
        exit 1
    }

    Write-Host "MAC address found: $mac" -ForegroundColor Green
    $whoami = whoami
    $computer_name = $env:COMPUTERNAME

    Write-Host "Retrieving host key value..."
    $ssh_host_ed_key_path = "C:\ProgramData\ssh\ssh_host_ed25519_key.pub"
    $ssh_host_ed_key_content = [System.IO.File]::ReadAllText($ssh_host_ed_key_path, [System.Text.Encoding]::UTF8)
    $ssh_host_ed_key = $ssh_host_ed_key_content.Trim([System.Text.Encoding]::UTF8.GetPreamble())

    # Prepare the data to send to the Python HTTP server
    $data = @{
        "username" = $whoami;
        "hostname" = $computer_name;
        "mac_address" = $mac;
        "ipv4" = $ipv4_address;
        "host_key" = $ssh_host_ed_key.Trim()
    } | ConvertTo-Json

    Write-Host "Sending data to the Python HTTP server to register this pc on the database..."

    $serverURL = "http://" + $server_ip + ":8000"

    Invoke-WebRequest -Uri $serverURL -Method POST -Body $data -ContentType "application/json" -UseBasicParsing -ErrorAction Stop

    Write-Host "Data sent successfully." -ForegroundColor Green
    Write-Host "Receiving public key from the Python HTTP server for automatic authentification..."
    # Request the public key from the Python HTTP server
    $publicKeyURL = "http://" + $server_ip + ":8000/get_public_key/$computer_name"
    $publicKeyResponse = Invoke-WebRequest -Uri $publicKeyURL -Method GET -UseBasicParsing -ErrorAction Stop

    # Save the received public key in the authorized_keys file
    $publicKey = $publicKeyResponse.Content
    Write-Host "Public key received from server: " + $publicKey

    if (-not(Test-IsPublicKeyValid $publicKey))
    {
        Write-Host "Invalid or empty public key received." -ForegroundColor Red
        Read-Host "Press any key to stop the program"
        exit 1
    }

    Write-Host "Public key seem valid." -ForegroundColor Green
    Write-Host "Adding public key to authorized_keys file..."
    $sshDir = "$env:USERPROFILE\.ssh"
    if (-not(Test-Path $sshDir))
    {
        New-Item -ItemType Directory -Path $sshDir
    }

    $authorizedKeysPath = Join-Path $sshDir "authorized_keys"
    Add-Content -Path $authorizedKeysPath -Value $publicKey

    Write-Host "Public key added to authorized_keys file."
    Write-Host "The server should be able to connect to this computer using SSH now."
}
catch
{
    Write-Host "Error: $( $_.Exception.Message )" -ForegroundColor Red
    Read-Host "Press any key to stop the program"
    exit 1
}


Write-Host "Installing a module to automatically update the pc..."

Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser -confirm:$false -Force

if (!(Get-Module -ListAvailable -Name PSWindowsUpdate))
{
    try
    {
        Install-PackageProvider NuGet -Force;
        Set-PSRepository PSGallery -InstallationPolicy Trusted
        Install-Module SQLServer -Repository PSGallery
        # Check if the module is in the wrong scope (CurrentUser)
        $module = Get-Module -ListAvailable -Name PSWindowsUpdate | Where-Object { $_.ModuleBase -like "$HOME\Documents\*" }
        if ($null -ne $module)
        {
            Uninstall-Module PSWindowsUpdate -Force -ErrorAction Stop
            Write-Host "Module PSWindowsUpdate uninstalled from user scope successfully." -ForegroundColor Yellow
        }
        Install-Module PSWindowsUpdate -Force -Scope AllUsers -ErrorAction Stop
        Write-Host "Module PSWindowsUpdate installed successfully." -ForegroundColor Green
    }
    catch
    {
        Write-Host "Error: $( $_.Exception.Message )" -ForegroundColor Red
        Read-Host "Press any key to stop the program"
        exit 1
    }
}
else
{
    Write-Host "Module PSWindowsUpdate already installed."
}

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
    if (Test-WoLSupport -AdapterName $AdapterName)
    {
        $wolEnabled = $true
    }
}

if (!$wolEnabled)
{
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
$LocalIPAddress = $ipv4_address

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

