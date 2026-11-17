# Image & PDF Tools installer — run once: right-click Run with PowerShell
$ErrorActionPreference = "Stop"

$src  = Split-Path $MyInvocation.MyCommand.Path -Parent
$dest = "C:\Scripts\imagepdf"

# 1. Copy scripts
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item "$src\main.py", "$src\main.pyw", "$src\tools.py", `
          "$src\image_tools.py", "$src\pdf_tools.py", `
          "$src\tools_common.py", "$src\dialogs.py" -Destination $dest -Force

# 2. Dependencies — into the interpreter pyw.exe actually runs
$pyw = (Get-Command pyw.exe -ErrorAction SilentlyContinue).Source
if (-not $pyw) { $pyw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source }
if (-not $pyw) { throw "Python windowed launcher (pyw.exe) not found on PATH - install Python with the 'py launcher' option" }
& $pyw -m pip install pypdf --quiet
if ($LASTEXITCODE -ne 0) { throw "pip install pypdf failed" }

# 3. Registry: right-click submenu (HKCU — no admin needed)
reg import "$src\tools_menu.reg"
if ($LASTEXITCODE -ne 0) { throw "registry import failed" }

# 4. Send To shortcut for multi-file merge
$sendTo = [Environment]::GetFolderPath("ApplicationData") + "\Microsoft\Windows\SendTo"
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut("$sendTo\Merge PDFs.lnk")
$lnk.TargetPath = $pyw
$lnk.Arguments  = "`"C:\Scripts\imagepdf\main.pyw`" merge"
$lnk.IconLocation = "imageres.dll,-5372"
$lnk.Save()

Write-Host "Installed. Right-click any image or PDF -> 'Image & PDF Tools'."
Write-Host "Select multiple PDFs -> right-click -> Send To -> 'Merge PDFs'."
