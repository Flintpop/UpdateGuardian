Import-Module "../api/VMManagement.psm1"

# Liste des VMs à démarrer avec le nom de l'instantané correspondant
$vmsToStart = @{
    "linuxserver" = "ready";
#    "client udpate" = "Nouveaux shortcuts"
}

# Obtention de la liste des VMs disponibles
$availableVms = Get-AvailableVms

if ($availableVms.Count -eq 0) {
    Write-Error "Error: No VMs available."
    exit 1
}

if ($vmsToStart.Count -eq 0) {
    Write-Error "Error: No VMs to start."
    exit 1
}

# Si une VM à démarrer n'est pas dans la liste des VMs disponibles, on arrête le script
if ($vmsToStart.Keys | Where-Object { $_ -notin $availableVms }) {
    Write-Error "Error: One or more VMs to start are not available.
    Available VMs: $($availableVms -join ', ')
    VMs to start: $($vmsToStart.Keys -join ', ')"
    exit 1
}

# If the specifed snapshot does not exist, the script will stop
foreach ($vmName in $vmsToStart.Keys) {
    if (-not (Check-SnapshotExists $vmName $vmsToStart[$vmName])) {
        Write-Error "Error: Snapshot '$($vmsToStart[$vmName])' for VM '$vmName' does not exist."
        exit 1
    }
}


foreach ($vmName in $vmsToStart.Keys) {
    if (-not ($availableVms -contains $vmName)) {
        Write-Host "Error: VM '$vmName' not found in the list of available VMs."
        exit 1
    }

    if (Is-VMRunning $vmName) {
        Write-Host "VM: $vmName is already running."
        continue
    }

    # Restauration de l'instantané avant le démarrage
    Restore-Snapshot $vmName $vmsToStart[$vmName]

    # Démarrage de la VM
    Start-VM $vmName
}
