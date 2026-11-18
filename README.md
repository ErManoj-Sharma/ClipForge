# Image & PDF Tools — Documentation
opencode -s ses_e15c6c992ffe18SdPUSAueCMr2
A Windows right-click suite for image and PDF work. No app window: everything
lives in the Explorer context menu (plus a tiny dialog only when a "custom"
value is needed). All deployable files sit in the **`ImagePdfTools/`** folder —
copy that one folder to Windows; on the machine it deploys to `C:\Scripts\imagepdf`.

---

## 1. What you can do

**Right-click an image → "Image & PDF Tools"**

| Menu item                         | What it does                                                  |
|-----------------------------------|---------------------------------------------------------------|
| Convert to PDF                    | Image → one-page PDF                                          |
| Convert to PNG                    | Any image → `.png`                                            |
| Convert to JPG                    | Any image → `.jpg` (quality 90)                               |
| Resize to 50 / 100 / 150 / 300 KB | Shrink image until file size fits that ceiling                |
| Resize to Custom KB…              | Same, with a size you type                                    |
| Resize to Pixel Size…             | Fit image inside W × H you type (aspect kept, never upscales) |

**Right-click a PDF → "Image & PDF Tools"**

| Menu item                              | What it does                                                            |
|----------------------------------------|-------------------------------------------------------------------------|
| Convert to Images (PNG)                | Each page → `.png` at 200 dpi (multi-page: `file_1.png`, `file_2.png`…) |
| Split Every Page                       | `file.pdf` → `file_1.pdf`, `file_2.pdf`, … (one page each)              |
| Split Every N Pages…                   | Type N → chunks of N pages (`file_1-3.pdf`, `file_4-6.pdf`…)            |
| Compress to 100 / 500 KB / 1 MB / 2 MB | Rebuild the PDF smaller than that ceiling                               |
| Compress to Custom…                    | Type any KB target                                                      |
| Queue for Merge                        | Add to merge queue — on multi-select each file queues itself            |
| Merge Queued PDFs                      | Reorder + merge the queue, then clear it                                |

**Merging PDFs — three ways**

1. **Merge Selected PDFs (one step, right-click menu):** select 2+ PDFs →
   right-click → **Merge Selected PDFs** → a brief "Collecting selected
   PDFs…" window appears while the files are gathered, then the reorder dialog
   opens **once** with all of them (Up/Down sets page order, **Remove** drops
   a file) → **Merge**. Behind the scenes each selected file's invocation adds
   itself to a shared list and the first one (holding a lock that is held
   until the whole session ends) opens the dialog once — no matter how many
   files are selected, and later straggler processes never open a second
   dialog. A canceled or errored burst is wiped, so the next right-click
   starts fresh. Selecting a single PDF shows "Collecting…" for up to 8s
   (waiting for siblings that Explorer may spawn late) and then a clear
   error.
2. **Queue for Merge / Merge Queued PDFs (right-click menu, explicit):**
   select PDFs → **Queue for Merge** (queues each) → **Merge Queued PDFs** →
   reorder dialog → **Merge**. Queue clears on success, stays if you Cancel
   so you can retry.
3. **Send To (one step, legacy):** select the PDFs → right-click → **Send To →
   Merge PDFs** — Explorer passes all selected files at once, straight to the
   reorder dialog.

Result in all cases: `merged.pdf` next to the first file.

### Rules that apply everywhere
- Output is always saved **next to the input file**.
- The **input file is never overwritten**; if the output name exists, it gets
  `_1`, `_2`, … appended (`report.pdf` exists → `report_1.pdf`).
- Targets like "100 KB" are **ceilings, not exact sizes** — the tool gets as
  close as it can from above.
- If something fails, a message box explains it; no console window ever appears.

---

## 2. Install / Uninstall (one click)

### Install
**Double-click `setup.bat`.** It launches `setup.ps1` (you confirm one UAC
prompt — admin is needed to write `C:\Scripts\imagepdf` and `C:\poppler`).
The script checks, in order, and installs only what is missing:

1. **Python** — if `pyw.exe`/`pythonw.exe` isn't found: installs via `winget`
   (`Python.Python.3.12`), falling back to the python.org silent installer
   (`/quiet PrependPath=1 Include_launcher=1`), then re-detects the launcher.
2. **Python packages** — `pillow`, `img2pdf`, `pdf2image`, `pypdf`
   (`pip install` skips anything already present).
3. **Poppler** — `pdf2image` needs its DLLs. If
   `C:\poppler\poppler-24.08.0\Library\bin` is missing, the script downloads
   the pinned GitHub release (`oschwartz10612/poppler-windows v24.08.0-0`) and
   extracts it there — exactly the path the code hardcodes.
4. **Scripts** — copies the 7 `.py`/`.pyw` files to `C:\Scripts\imagepdf`.
5. **Registry + shortcut** — imports `tools_menu.reg` (right-click submenu)
   and creates `Send To\Merge PDFs.lnk` pointing at the detected launcher.

### Uninstall
**Double-click `uninstall.bat`** (runs `uninstall.ps1`). It removes the two
registry keys (the whole submenu) and the Send To shortcut. It deliberately
**leaves** `C:\Scripts\imagepdf`, Python, the packages, and Poppler installed
(general-purpose tools other things may use) — delete `C:\Scripts\imagepdf`
manually if you want a fully clean machine. `uninstall_tools.reg` alone does
just the registry part.

### Windows 11 note
Win11's compact menu hides classic verbs behind **Show more options**. Setup
restores the **classic full menu as the default first menu** (one HKCU key,
Explorer restart — setup asks before restarting). That puts Image & PDF Tools
on the first right-click. Running `uninstall.bat` reverts Windows 11 to its
default compact menu. (If a future Windows update re-enables the compact
menu, re-run `setup.bat`.) To restore the default compact menu **without**
uninstalling the tools, double-click `restore_default_menu.bat`; run
`setup.bat` again to switch back to the classic menu.

### Manual install/uninstall without PowerShell
Double-click `tools_menu.reg` to add the menu; double-click
`uninstall_tools.reg` to remove it. (Everything else still needs setup/uninstall.)

---

## 3. How it works

### 3.1 The chain: right-click → registry → pyw → router

```
You right-click a file
        │
        ▼
Registry (HKCU\Software\Classes\SystemFileAssociations\image\.pdf\shell)
        │  MUIVerb "Image & PDF Tools" + nested shell\NN_<verb>\command keys
        ▼
pyw.exe "C:\Scripts\imagepdf\main.pyw" <action> "<file path>"
        │  pyw = the windowless Python launcher → no console flash
        ▼
main.py  dispatch(argv)  →  routes <action> to the matching function
```

- `main.pyw` is a 1-line launcher that imports `main.dispatch` (`.pyw` files
  can't be imported directly, which is why the logic lives in `main.py`).
- `tools.py` re-exports all tool functions so the router calls them through
  one patchable namespace (used by the tests).
- Registry is under **HKCU** (per-user): no admin needed, survives for your
  account only.
- The **Merge PDFs** entry is in the **Send To** menu instead, because Send To
  is the only Explorer path that passes *all selected files* to the command in
  one go — ordinary context-menu verbs fire once per file (merge would run 4
  times instead of once).

### 3.2 Files (in the `ImagePdfTools/` folder; deployed copies live in `C:\Scripts\imagepdf`)

| File                                    | Responsibility                               |
|-----------------------------------------|----------------------------------------------|
| `tools_common.py`                       | `unique_path()` — non-colliding output names |
| `image_tools.py`                        | image conversions + resizes                  |
| `pdf_tools.py`                          | PDF merge / split / compress / to-images     |
| `dialogs.py`                            | the three tiny Tkinter dialogs               |
| `main.py` + `main.pyw`                  | action router + windowless entry point       |
| `tools.py`                              | namespace re-export (test seam)              |
| `tools_menu.reg`, `uninstall_tools.reg` | registry add / remove                        |
| `setup.ps1`, `setup.bat`                | one-click install (+ double-click wrapper)   |
| `uninstall.ps1`                         | one-step uninstall                           |

Pre-existing legacy scripts (`context_menu.reg`, `image_to_pdf.py`,
`image_to_png.py`, `pdf_to_jpeg.py`, `pdf_to_png.py`, `pdf_to_png.reg`,
`send_to_wsl.reg`, `SendToWSL.ps1`, `update_icons.reg`) are the older flat
menu versions — they still work and are independent of this suite.

### 3.3 Each feature, internally

**Image → PDF** (`img2pdf.convert`) — lossless embedding, output `.pdf`.

**Image → PNG / JPG** (`Pillow`) — converted to RGBA / RGB and saved; JPG at
quality 90.

**Resize to KB** — the image is JPEG-encoded at quality 95, then a **binary
search over quality 95→1** finds the highest quality whose byte size fits the
target (each step encodes to memory, never touches disk). If even quality 1
is still too big, the **smallest attempt** is written (best effort). Output
`.jpg`.

**Resize to pixel size** — `Image.thumbnail(W, H)`: fits *inside* the box
keeping aspect ratio; never upscales a smaller image. PNG stays PNG, others
become JPG.

**PDF → Images** — `pdf2image.convert_from_path` at **200 dpi** using the
Poppler DLLs at `C:\poppler\poppler-24.08.0\Library\bin` (move Poppler and
this path must change). One PNG per page, `_1`, `_2`… suffixes on multi-page.

**Split** — `pypdf` reads the page count, then each output writer copies a
page range. Every-page: `file_1.pdf`…; every-N: ranges `1-3`, `4-6`, `7-7`
(last chunk may be smaller).

**Merge** — `pypdf.PdfWriter.append()` for each file in the order you set in
the reorder dialog → `merged.pdf`.

**Compress to KB** — there is no library that compresses arbitrary PDFs to an
exact size, so the pages are **rasterized** and the PDF is rebuilt from page
images. The algorithm **maximizes quality under the target**: for each dpi
(200 → 150 → 110 → 72 → 50 → 40) it binary-searches, in order, **color JPEG
quality, grayscale JPEG quality, then palette-PNG color count** for the
largest result that fits — the first dpi/mode where anything fits wins, so
output lands just under the target (e.g. 98 KB for a 100 KB request). Dense
screenshot PDFs usually need grayscale or palette PNG at lower dpi; photo
PDFs fit as color JPEG at high dpi. Pages render once per dpi (expensive);
the searches re-encode in memory (cheap). **Lossy** — pages become images,
text becomes non-selectable; very dense content may need low dpi to hit the
target, which is a physical limit, not a bug.

### 3.4 The dialogs (`dialogs.py`)

Borderless always-on-top Tk windows, centered on screen:

- **ask_value** — one entry + OK. Enter = OK, Esc = cancel (returns None,
  which aborts the action — no file is written).
- **ask_pixel_size** — parses `1280 x 720` (also `*`); invalid input stays in
  the window with a hint instead of closing.
- **reorder_dialog** — listbox + Up/Down + Merge/Cancel for the merge order.
  Selection is cleared before re-set because Tk's `selection_set` proved
  additive in this build.

### 3.5 Error handling

`main.dispatch` wraps everything in a try/except that shows the error in a Tk
message box — important because `pyw.exe` has no console, so an unhandled
crash would otherwise fail silently. Cancelled dialogs and bad input never
write files.

---

## 4. Testing

29 automated tests (`python3 -m pytest`, all passing) cover the pure logic:
collision naming, resize binary search + best-effort floor, split chunking,
compress early-return + ladder stop, merge order, and the router's action
table (dialog cancellation aborting, unknown actions, merge needing ≥ 2
files). The GUI dialogs were verified interactively; Windows-side behavior
(registry, Send To, installer) is read-verified only — the first real run on
Windows is the final test.

## 5. Known limits

- PDF compress is lossy (rasterized pages).
- Size targets are ceilings, not exact values.
- Single-file menu verbs act on one file; Explorer's per-file firing is why
  merge uses Send To.
- Merge accepts whatever files you send (it doesn't filter by extension);
  a non-PDF will surface an error box.
- Poppler path is hardcoded; moving `C:\poppler` requires updating
  `pdf_tools.py` (`POPLER`).
- The cascaded submenu uses the common-but-semi-documented `SubCommands=""`
  pattern; if the submenu appears empty on your Windows build, the parent
  key needs `ExtendedSubCommandsKey` instead (one-line registry change).
