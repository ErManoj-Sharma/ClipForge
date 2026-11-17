param(
    [string]$File
)

if (!(Test-Path $File)) {
    Write-Host "File not found: $File"
    exit 1
}

$File = (Resolve-Path $File).Path

$drive = $File.Substring(0,1).ToLower()
$rest = $File.Substring(2).Replace('\','/')

$wslPath = "/mnt/$drive$rest"

Write-Host "Windows: $File"
Write-Host "WSL: $wslPath"

wsl mkdir -p /home/manoj/WindowsData
wsl cp "$wslPath" /home/manoj/WindowsData/

Write-Host "Copied successfully"