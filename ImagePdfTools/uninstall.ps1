# Image & PDF Tools uninstaller
$ErrorActionPreference = "Stop"
$src = Split-Path $MyInvocation.MyCommand.Path -Parent

reg import "$src\uninstall_tools.reg"
if ($LASTEXITCODE -ne 0) { throw "registry import failed" }

# restore Win11's default compact menu (undo the setup.ps1 tweak)
reg delete "HKCU\Software\Classes\CLSID\{86ca1e77-a88c-4dc8-a587-e0cb6b5d8fb5}" /f 2>$null | Out-Null
$ans = Read-Host "Restart Explorer now to apply? [Y/n]"
if ($ans -notmatch '^n') { Stop-Process -Name explorer -Force }

$lnk = [Environment]::GetFolderPath("ApplicationData") + "\Microsoft\Windows\SendTo\Merge PDFs.lnk"
if (Test-Path $lnk) { Remove-Item $lnk -Force }

Write-Host "Uninstalled. (C:\Scripts\imagepdf kept; delete it manually if you want.)"
