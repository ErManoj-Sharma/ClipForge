# ============================================================
# Image & PDF Tools - one-click installer
# Double-click setup.bat (or right-click this file -> Run with PowerShell).
# Installs everything that is missing, then wires up the right-click menu.
# ============================================================
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# --- self-elevate: needs admin for C:\Scripts and C:\poppler ---
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList `
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`""
    exit
}

Write-Host "=== Image & PDF Tools installer ==="

$dest    = "C:\Scripts\imagepdf"
$src     = Split-Path $MyInvocation.MyCommand.Path -Parent
$poppler = "C:\poppler\poppler-24.08.0\Library\bin"

# ---------- 1. Python (with windowed launcher) ----------
function Find-Pyw {
    $c = (Get-Command pyw.exe -ErrorAction SilentlyContinue).Source
    if ($c) { return $c }
    $c = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
    if ($c) { return $c }
    $hit = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\*\pythonw.exe" -ErrorAction SilentlyContinue |
           Select-Object -First 1 -ExpandProperty FullName
    if ($hit) { return $hit }
    $hit = Get-ChildItem "C:\Python*\pythonw.exe", "C:\Program Files\Python*\pythonw.exe" -ErrorAction SilentlyContinue |
           Select-Object -First 1 -ExpandProperty FullName
    return $hit
}

$pyw = Find-Pyw
if (-not $pyw) {
    Write-Host "Python not found - installing (this takes a few minutes)..."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install -e --id Python.Python.3.12 --scope user `
            --accept-package-agreements --accept-source-agreements
    } else {
        $installer = "$env:TEMP\python-installer.exe"
        Invoke-WebRequest "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe" -OutFile $installer
        Start-Process $installer -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_launcher=1" -Wait
        Remove-Item $installer -Force
    }
    # fresh PATH from registry, then retry
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
    $pyw = Find-Pyw
    if (-not $pyw) { throw "Python was installed but pythonw.exe was not found. Re-run this script after reopening PowerShell." }
}
Write-Host "Python launcher: $pyw"

# ---------- 2. Python packages (pip skips anything already installed) ----------
& $pyw -m pip install --quiet pillow img2pdf pdf2image pypdf
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
Write-Host "Python packages OK"

# ---------- 3. Poppler (pdf2image needs its DLLs) ----------
if (-not (Test-Path $poppler)) {
    Write-Host "Poppler not found - downloading..."
    $zip = "$env:TEMP\poppler.zip"
    Invoke-WebRequest "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip" -OutFile $zip
    New-Item -ItemType Directory -Force -Path "C:\poppler" | Out-Null
    Expand-Archive $zip "C:\poppler" -Force
    Remove-Item $zip -Force
}
if (-not (Test-Path $poppler)) { throw "Poppler install failed" }
Write-Host "Poppler OK"

# ---------- 4. Copy scripts ----------
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item "$src\main.py", "$src\main.pyw", "$src\tools.py", `
          "$src\image_tools.py", "$src\pdf_tools.py", `
          "$src\tools_common.py", "$src\dialogs.py" -Destination $dest -Force

# ---------- 5. Registry + Send To shortcut ----------
# The .reg is a template: __PYW__ is replaced with the absolute launcher path.
# Context-menu commands must launch an executable - a bare .pyw document is
# never executed, and bare "pyw.exe" breaks when the launcher is not on PATH.
$pywEsc = $pyw.Replace('\', '\\')
$menu = Get-Content "$src\tools_menu.reg" -Raw
$menu = $menu.Replace('__PYW__', $pywEsc)
$gen = "$env:TEMP\tools_menu_generated.reg"
Set-Content -Path $gen -Value $menu -Encoding Unicode
reg import "$gen"
if ($LASTEXITCODE -ne 0) { throw "registry import failed" }

if (-not (Test-Path "$dest\main.pyw")) { throw "scripts were not copied to $dest" }

$sendTo = [Environment]::GetFolderPath("ApplicationData") + "\Microsoft\Windows\SendTo"
$ws  = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut("$sendTo\Merge PDFs.lnk")
$lnk.TargetPath   = $pyw
$lnk.Arguments    = "`"C:\Scripts\imagepdf\main.pyw`" merge"
$lnk.IconLocation = "imageres.dll,-5372"
$lnk.Save()

Write-Host ""
Write-Host "Installed."
Write-Host "  Right-click any image or PDF  -> 'Image & PDF Tools'"
Write-Host "  Select PDFs -> right-click    -> Send To -> 'Merge PDFs'"
Read-Host "Press Enter to close"
