# Define the log file path as a variable for easier modification
Import-Module PSWindowsUpdate
$logFilePath = "C:\Temp\UpdateGuardian\update_powershell_log.txt"
$jsonFilePath = "C:\Temp\UpdateGuardian\update_status.json"

# Function to log messages with timestamps
function Write-Log {
    param (
        [Parameter(Mandatory=$true)]
        [string] $Message
    )
    "$((Get-Date).ToString()): $Message" | Out-File -Append -FilePath $logFilePath -Encoding UTF8
}

# Function to write update status to JSON file
function Write-JSON {
    param (
        [Parameter(Mandatory=$true)]
        [pscustomobject] $UpdateStatus
    )
    $UpdateStatus | ConvertTo-Json -Depth 100 | Set-Content -Path $jsonFilePath -Encoding UTF8
}

# Initialize JSON object
$updateStatus = @{
    UpdateCount = 0;
    UpdateNames = @();
    UpdateFinished = $false;
    ErrorMessage = $null
}

# Write initial JSON status
Write-JSON -UpdateStatus $updateStatus

# Clear the log file at the start of the script
if (-not (Test-Path $logFilePath)) {
    New-Item -ItemType File -Path $logFilePath | Out-Null
}

# Start the script
Write-Log "Script started"

try {
    # Check for updates
    Write-Log "Checking for updates..."
    $updateResult = Get-WindowsUpdate

    # Check if there are any updates that are not installed
    $updatesToInstall = $updateResult.Updates | Where-Object { -not $_.IsInstalled }
    if ($null -eq $updatesToInstall -or $updatesToInstall.Count -eq 0){
        Write-Log "No updates found"
        Write-Log "Script ended"
        $updateStatus.UpdateFinished = $true
        Write-JSON -UpdateStatus $updateStatus
        exit 0
    }

    foreach ($update in $updateResult.Updates) {
        if ($update.IsInstalled -eq $false) {
            Write-Log "Update found: $($update.Title)"
            # Update JSON status
            $updateStatus.UpdateCount++
            $updateStatus.UpdateNames += $update.Title
            Write-JSON -UpdateStatus $updateStatus
        }
    }

    Write-Log "Downloading updates..."
    Get-WindowsUpdate -Download -AcceptAll *>> $logFilePath

    Write-Log "Installing updates..."
    Get-WindowsUpdate -Install -AcceptAll -AutoReboot *>> $logFilePath

    Write-Log "Update process completed"
    # Update JSON status
    $updateStatus.UpdateFinished = $true
    Write-JSON -UpdateStatus $updateStatus

} catch {
    # Handle exceptions and log the error details
    $ErrorMessage = $_.Exception.Message
    $FailedItem = $_.Exception.ItemName
    Write-Log "Error: $ErrorMessage"
    Write-Log "Item that caused the error: $FailedItem"
    # Update JSON status
    $updateStatus.ErrorMessage = "Error: $ErrorMessage. Item that caused the error: $FailedItem"
    Write-JSON -UpdateStatus $updateStatus
}

# End the script
Write-Log "Script ended"
