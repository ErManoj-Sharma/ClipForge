# Image & PDF Tools uninstaller
$ErrorActionPreference = "Stop"
$src = Split-Path $MyInvocation.MyCommand.Path -Parent

reg import "$src\uninstall_tools.reg"
if ($LASTEXITCODE -ne 0) { throw "registry import failed" }

$lnk = [Environment]::GetFolderPath("ApplicationData") + "\Microsoft\Windows\SendTo\Merge PDFs.lnk"
if (Test-Path $lnk) { Remove-Item $lnk -Force }

Write-Host "Uninstalled. (C:\Scripts\imagepdf kept; delete it manually if you want.)"
