try {
    $UpdateSession = New-Object -ComObject Microsoft.Update.Session
    $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
    $SearchResult = $UpdateSearcher.Search("IsInstalled=0 and Type='Software' and IsHidden=0")
    $Updates = $SearchResult.Updates

    if ($Updates.Count -eq 0) {
        Write-Host "No updates available."
        exit 3
    } else {
        Write-Host "Found $($Updates.Count) updates."

        # Filter out updates that are already downloaded or being downloaded
        $UpdatesToDownload = @()
        foreach ($Update in $Updates) {
            if (-not $Update.IsDownloaded -and $Update.DownloadPriority -eq 1) {
                $UpdatesToDownload += $Update
            }
        }

        if ($UpdatesToDownload.Count -eq 0) {
            Write-Host "No updates to download."
            exit 0
        }

        $Downloader = $UpdateSession.CreateUpdateDownloader()
        $Downloader.Updates = $UpdatesToDownload
        Write-Host "Downloading updates..."
        $DownloadResult = $Downloader.Download()

        if ($DownloadResult.HResult -ne 0) {
            Write-Host "Error downloading updates. Error code: $($DownloadResult.HResult)"
            exit 1
        }

        $UpdatesToInstall = New-Object -TypeName Microsoft.Update.UpdateColl

        for ($i = 0; $i -lt $UpdatesToDownload.Count; $i++) {
            if ($UpdatesToDownload[$i].IsDownloaded) {
                $UpdatesToInstall.Add($UpdatesToDownload[$i]) | Out-Null
            }
        }

        if ($UpdatesToInstall.Count -eq 0) {
            Write-Host "No updates downloaded. Exiting..."
            exit 1
        }

        $Installer = $UpdateSession.CreateUpdateInstaller()
        $Installer.Updates = $UpdatesToInstall
        Write-Host "Installing updates..."
        $InstallationResult = $Installer.Install()

        if ($InstallationResult.HResult -ne 0) {
            Write-Host "Error installing updates. Error code: $($InstallationResult.HResult)"
            exit 1
        }

        if ($InstallationResult.RebootRequired) {
            Write-Host "Reboot required."
            exit 2
        }
        else {
            Write-Host "Updates installed successfully."
            exit 0
        }
    }
} catch {
    Write-Host "An error occurred: $($_.Exception.Message)"
    exit 1
}
