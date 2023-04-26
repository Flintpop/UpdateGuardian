try {
    $UpdateSession = New-Object -ComObject Microsoft.Update.Session
    $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
    $SearchResult = $UpdateSearcher.Search("IsInstalled=0 and Type='Software' and IsHidden=0")
    $Updates = $SearchResult.Updates

    if ($Updates.Count -eq 0) {
        Write-Host "No updates available."
    } else {
        Write-Host "Found $($Updates.Count) updates."

        $Downloader = $UpdateSession.CreateUpdateDownloader()
        $Downloader.Updates = $Updates
        Write-Host "Downloading updates..."
        $DownloadResult = $Downloader.Download()

        if ($DownloadResult.HResult -ne 0) {
            Write-Host "Error downloading updates. Error code: $($DownloadResult.HResult)"
            exit 1
        }

        $UpdatesToInstall = New-Object -TypeName Microsoft.Update.UpdateColl

        for ($i = 0; $i -lt $Updates.Count; $i++) {
            if ($Updates.Item($i).IsDownloaded) {
                $UpdatesToInstall.Add($Updates.Item($i)) | Out-Null
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

        Write-Host "Installation Result: $($InstallationResult.ResultCode)"
        Write-Host "Reboot required: $($InstallationResult.RebootRequired)"
    }
} catch {
    Write-Host "An error occurred: $($_.Exception.Message)"
    exit 1
}
