# ============================================================
# RightKit Image and Pdf Tools - one-click installer
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

Write-Host "=== RightKit Image and Pdf Tools installer ==="

$dest    = "C:\Scripts\imagepdf"
$version = "1.0.2"
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

# ---------- 3. Visual C++ Redistributable (Poppler's pdfinfo.exe needs it) ----------
# pdfinfo.exe fails to start without MSVCP140.dll ("The code execution cannot
# proceed because MSVCP140.dll Was not found"), which turns every PDF
# conversion/compress into "PDFPageCountError: Unable to get page count".
$vsRuntime = "$env:SystemRoot\System32\msvcp140.dll"
if (-not (Test-Path $vsRuntime)) {
    Write-Host "Visual C++ runtime (MSVCP140.dll) missing - installing..."
    $redist = "$env:TEMP\vc_redist.x64.exe"
    Invoke-WebRequest "https://aka.ms/vs/17/release/vc_redist.x64.exe" -OutFile $redist
    Start-Process -FilePath $redist -ArgumentList "/install", "/quiet", "/norestart" -Wait
    Remove-Item -Force $redist
    if (-not (Test-Path $vsRuntime)) {
        throw "MSVCP140.dll still missing after install - install the Visual C++ Redistributable from https://aka.ms/vs/17/release/vc_redist.x64.exe and re-run setup"
    }
}

# ---------- 4. Poppler (pdf2image needs its DLLs) ----------
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

# ---------- 5. Copy scripts ----------
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item "$src\main.py", "$src\main.pyw", "$src\tools.py", `
          "$src\image_tools.py", "$src\pdf_tools.py", `
          "$src\tools_common.py", "$src\dialogs.py" -Destination $dest -Force
# keep the uninstaller + RightKit icon alongside the installed files (both are
# present in the packaged installer)
foreach ($f in 'uninstall.ps1', 'uninstall.bat', 'uninstall_tools.reg',
              'rightkit.ico') {
  if (Test-Path "$src\$f") { Copy-Item "$src\$f" -Destination $dest -Force }
}
# version file the 'Check for Update' action compares against
Set-Content -LiteralPath "$dest\version.txt" -Value $version -Encoding UTF8

# ---------- 6. Registry + Send To shortcut ----------
# The .reg is a template: __PYW__ is replaced with the absolute launcher path.
# Context-menu commands must launch an executable - a bare .pyw document is
# never executed, and bare "pyw.exe" breaks when the launcher is not on PATH.
$pywEsc = $pyw.Replace('\', '\\')
$menu = Get-Content "$src\tools_menu.reg" -Raw
$menu = $menu.Replace('__PYW__', $pywEsc)
$gen = "$env:TEMP\tools_menu_generated.reg"
Set-Content -Path $gen -Value $menu -Encoding Unicode

# reg import only adds/overwrites - it never deletes verbs that were renamed or
# removed in a later version. Wipe the whole old submenu tree first (in both
# hives) so stale keys like 01_ConvertToImages cannot linger as a second
# "Convert to Images (PNG)" row. Also drop the legacy flat duplicate entries.
foreach ($root in 'HKCU:\Software\Classes', 'HKLM:\Software\Classes') {
  foreach ($key in 'SystemFileAssociations\.pdf\shell\ImagePdfTools',
                   'SystemFileAssociations\image\shell\ImagePdfTools',
                   'SystemFileAssociations\.pdf\shell\ConvertToPNG',
                   'SystemFileAssociations\.pdf\shell\ConvertToJPEG',
                   'SystemFileAssociations\image\shell\ConvertToPDF',
                   'SystemFileAssociations\image\shell\ConvertToPNG') {
    $p = Join-Path $root $key
    if (Test-Path $p) { Remove-Item -Recurse -Force $p -ErrorAction SilentlyContinue }
  }
}

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

# ---------- 7. Windows 11: show the full (classic) menu on first right-click ----------
# Win11's compact menu hides classic verbs behind "Show more options"; a static
# verb cannot be added to the new menu without an MSIX package. Restoring the
# classic menu puts RightKit Image and Pdf Tools on the first right-click.
reg add "HKCU\Software\Classes\CLSID\{86ca1e77-a88c-4dc8-a587-e0cb6b5d8fb5}\InprocServer32" /f /ve | Out-Null
if ($LASTEXITCODE -ne 0) { throw "failed to restore classic context menu" }
$ans = Read-Host "Restart Explorer now to apply the classic menu? [Y/n]"
if ($ans -notmatch '^n') { Stop-Process -Name explorer -Force }

Write-Host ""
Write-Host "Installed."
Write-Host "  Right-click any image or PDF  -> 'RightKit Image and Pdf Tools'"
Write-Host "  Select PDFs -> right-click    -> Send To -> 'Merge PDFs'"
Read-Host "Press Enter to close"
