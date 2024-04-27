function Get-AvailableVMs {
    return (VBoxManage list vms | ForEach-Object { if ($_ -match '"(.+)" \{') { $matches[1] } })
}

function Is-VMRunning($vmName) {
    $vmInfo = VBoxManage showvminfo $vmName --machinereadable
    return $vmInfo -match 'VMState="running"'
}

function Check-SnapshotExists($vmName, $snapshotName) {
    $snapshots = VBoxManage snapshot $vmName list --machinereadable
    $pattern = [regex]::Escape($snapshotName)
    return $snapshots -match $pattern
}


function Restore-Snapshot($vmName, $snapshotName) {
    if (-not (Check-SnapshotExists $vmName $snapshotName)) {
        throw "Snapshot '$snapshotName' for VM '$vmName' does not exist."
    }
    VBoxManage snapshot $vmName restore $snapshotName
}

function Start-VM($vmName) {
    VBoxManage startvm $vmName
}

Export-ModuleMember -Function Get-AvailableVMs, Is-VMRunning, Check-SnapshotExists, Restore-Snapshot, Start-VM