"""Build one shareable file: dist/RightKitSetup.cmd

The .cmd embeds a base64 ZIP of every deployable file. Double-clicking it
extracts to %TEMP% and runs setup.ps1, which self-elevates and installs
everything (Python, pip packages, Poppler, registry menu).

Re-run after changing any packaged file:

    python3 build_installer.py
"""
import base64
import io
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "dist", "RightKitSetup.cmd")
MARKER = "#PAYLOAD#"

FILES = [
    "main.py", "main.pyw", "tools.py", "image_tools.py", "pdf_tools.py",
    "tools_common.py", "dialogs.py",
    "setup.ps1", "setup.bat", "tools_menu.reg",
    "uninstall.ps1", "uninstall.bat", "uninstall_tools.reg",
    "remove_duplicate_png.reg",
    "rightkit.ico",
]

# The base64 blob is appended after "exit /b", so cmd never parses it.
STUB = r'''@echo off
setlocal
set "TMPD=%TEMP%\RightKitSetup"
if exist "%TMPD%" rmdir /s /q "%TMPD%" >nul 2>&1
mkdir "%TMPD%" >nul 2>&1
echo Extracting RightKit...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$t=[IO.File]::ReadAllText('%~f0');$m='__MARKER__';$b=$t.Substring($t.LastIndexOf($m)+$m.Length);[IO.File]::WriteAllBytes('%TMPD%\p.zip',[Convert]::FromBase64String($b))"
if not exist "%TMPD%\p.zip" (echo Extraction failed. & pause & exit /b 1)
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%TMPD%\p.zip' -DestinationPath '%TMPD%' -Force"
powershell -NoProfile -ExecutionPolicy Bypass -File "%TMPD%\setup.ps1"
exit /b
__MARKER__
'''


def build_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            z.write(os.path.join(HERE, name), name)
    return buf.getvalue()


def render():
    payload = base64.b64encode(build_zip()).decode("ascii")
    stub = STUB.replace("__MARKER__", MARKER).replace("\n", "\r\n")
    body = "\r\n".join(payload[i:i + 76] for i in range(0, len(payload), 76))
    return stub + body + "\r\n"


def build(out=OUT):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(render().encode("ascii"))
    return out


if __name__ == "__main__":
    path = build()
    print(f"wrote {path} ({os.path.getsize(path)} bytes)")
