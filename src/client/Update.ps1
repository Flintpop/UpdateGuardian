# Define the log file path as a variable for easier modification
Import-Module PSWindowsUpdate
$logFilePath = "C:\Temp\UpdateGuardian\update_powershell_log.txt"
$jsonFilePath = "C:\Temp\UpdateGuardian\update_status.json"
$lockFilePath = "C:\Temp\UpdateGuardian\update_status.lock"

# Function to log messages with timestamps
function Write-Log
{
    param (
        [Parameter(Mandatory = $true)]
        [string] $Message,
        [Parameter(Mandatory = $false)]
        [int] $new_lines
    )
    if (-not $PSBoundParameters.ContainsKey('new_lines'))
    {
        $new_lines = 0
    }

    $new_lines_str = "`n" * $new_lines
    "$new_lines_str$((Get-Date).ToString() ): $Message" | Out-File -Append -FilePath $logFilePath -Encoding UTF8
}



# Fonction modifiée pour attendre le fichier de verrouillage jusqu'à 10 secondes avant de forcer l'écriture
function Write-JSON {
    param (
        [Parameter(Mandatory = $true)]
        [pscustomobject] $UpdateStatus
    )

    $lockExists = Test-Path -Path $lockFilePath
    $waitTime = 0

    # Attendre jusqu'à 10 secondes pour que le fichier de verrouillage disparaisse
    if ($lockExists) {
        Write-Log "INFO: Lock file detected. Waiting for lock file to be removed before writing JSON."
    }
    while ($lockExists -and $waitTime -lt 10) {
        Start-Sleep -Seconds 1
        $lockExists = Test-Path -Path $lockFilePath
        $waitTime++
    }

    # Si le fichier de verrouillage existe toujours après 10 secondes, log un avertissement et le supprime
    if ($lockExists) {
        Write-Log "WARNING: Lock file still exists after waiting. Attempting to override and write JSON."
        Remove-Item -Path $lockFilePath -Force
    }

    # Création du fichier de verrouillage
    Write-Log "INFO: Creating lock file to prevent concurrent writes to JSON file."
    New-Item -Path $lockFilePath -ItemType File -Force | Out-Null

    # Écriture dans le fichier JSON
    $UpdateStatus | ConvertTo-Json -Depth 100 | Out-File -FilePath $jsonFilePath -Encoding UTF8

    # Suppression du fichier de verrouillage
    Write-Log "INFO: Removing lock file after writing JSON."
    Remove-Item -Path $lockFilePath -Force
}

# Initialize JSON object
$updateStatus = @{
    UpdateCount = 0;
    UpdateNames = @();
    UpdateFinished = $false;
    ErrorMessage = $null
    RebootRequired = $false
}

# Write initial JSON status
Write-JSON -UpdateStatus $updateStatus

# Clear the log file at the start of the script
if (-not(Test-Path $logFilePath))
{
    New-Item -ItemType File -Path $logFilePath | Out-Null
}

Out-File -FilePath $logFilePath -Encoding UTF8 -Force
# Start the script
Write-Log "Script started"

try
{
    # Check for updates
    Write-Log "Checking for updates..." -new_lines 1

    $updateResult = Get-WindowsUpdate -IgnoreReboot

    # Check if there are any updates that are not installed
    $updatesToInstall = @()
    foreach ($update in $updateResult)
    {
        if ($update.IsInstalled -eq $false)
        {
            $updatesToInstall += $update
        }
    }

    if ($null -eq $updatesToInstall -or $updatesToInstall.Count -eq 0)
    {
        Write-Log "No updates found" -new_lines 1
        Write-Log "Script ended"
        $updateStatus.UpdateFinished = $true
        Write-JSON -UpdateStatus $updateStatus
        exit 0
    }


    Write-Log "Updates found: $( $updatesToInstall.Count )" -new_lines 1
    foreach ($update in $updatesToInstall)
    {
        Write-Log "Update found: $( $update.Title )"
        # Update JSON status
        $updateStatus.UpdateCount++
        $updateStatus.UpdateNames += $update.Title
        Write-JSON -UpdateStatus $updateStatus
    }

    Write-Log "Downloading updates..." -new_lines 1
    $output = Get-WindowsUpdate -Download -AcceptAll -IgnoreReboot | Out-String
    Write-Log $output

    Write-Log "Installing updates..." -new_lines 1
    $output = Get-WindowsUpdate -Install -AcceptAll -IgnoreReboot | Out-String
    Write-Log $output


    Write-Log "Update process completed" -new_lines 1
    $updateStatus.UpdateFinished = $true
    Write-JSON -UpdateStatus $updateStatus

    $PendingReboot = Get-ItemProperty -Path 'HKLM:\Software\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired' -ErrorAction SilentlyContinue
    if ($PendingReboot)
    {
        Write-Log "A reboot is required" -new_lines 1
        $updateStatus.RebootRequired = $true
        Write-JSON -UpdateStatus $updateStatus
        Write-Log "Rebooting in 5 seconds..."
        Write-Log "Script ended"

        Start-Sleep -Seconds 5
        Get-WindowsUpdate -AutoReboot
    }
    else
    {
        Write-Log "No reboot required" -new_lines 1
    }
}
catch
{
    # Handle exceptions and log the error details
    $ErrorMessage = $_.Exception.Message
    $FailedItem = $_.Exception.ItemName
    Write-Log "Error: $ErrorMessage"
    Write-Log "Item that caused the error: $FailedItem"
    # Update JSON status
    $updateStatus.ErrorMessage = "Error: $ErrorMessage. `nItem that caused the error: $FailedItem"
    Write-JSON -UpdateStatus $updateStatus
}

# End the script
Write-Log "Script ended"
