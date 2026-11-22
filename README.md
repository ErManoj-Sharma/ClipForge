# RightKit Image and Pdf Tools — Documentation
A Windows right-click suite for image and PDF work. No app window: everything
lives in the Explorer context menu (plus a tiny dialog only when a "custom"
value is needed). All deployable files sit in the **`ImagePdfTools/`** folder —
copy that one folder to Windows; on the machine it deploys to `C:\Scripts\imagepdf`.

---

## 1. What you can do

**Right-click an image → "RightKit Image and Pdf Tools"**

Items are grouped with separator lines — conversions first, then resizes, then
Contact Developer.

| Menu item                         | What it does                                                  |
|-----------------------------------|---------------------------------------------------------------|
| Convert to PDF                    | Image → one-page PDF                                          |
| Convert to PNG                    | Any image → `.png`                                            |
| Convert to JPG                    | Any image → `.jpg` (quality 90)                               |
| Resize to 50 / 100 / 150 / 300 KB | Shrink image until file size fits that ceiling                |
| Resize to Custom KB…              | Same, with a size you type                                    |
| Resize to Pixel Size…             | Fit image inside W × H you type (aspect kept, never upscales) |
| Contact Developer                 | Opens the developer's links page in your browser              |

**Right-click a PDF → "RightKit Image and Pdf Tools"**

Groups, separated by lines: **merge**, **convert**, **split**, **compress**,
then **Contact Developer**.

| Menu item                              | What it does                                                            |
|----------------------------------------|-------------------------------------------------------------------------|
| Merge Selected PDFs                    | 2+ selected: merge dialog. 1 selected: adds it to the merge queue       |
| Queue for Merge                        | Add to merge queue — on multi-select each file queues itself            |
| Merge Queued PDFs                      | Reorder + merge the queue, then clear it                                |
| Convert to Images (PNG)                | Each page → `.png` at 200 dpi (multi-page: `file_1.png`, `file_2.png`…) |
| Convert to Images (JPG)                | Each page → `.jpg` at 200 dpi, quality 90 — much smaller for photo pages |
| Split Every Page                       | `file.pdf` → `file_1.pdf`, `file_2.pdf`, … (one page each)              |
| Split Every N Pages…                   | Type N → chunks of N pages (`file_1-3.pdf`, `file_4-6.pdf`…)            |
| Compress to 100 / 500 KB / 1 MB / 2 MB | Rebuild the PDF smaller than that ceiling                               |
| Compress to Custom…                    | Type any KB target                                                      |
| Contact Developer                      | Opens the developer's links page in your browser                        |

**Merging PDFs — three ways**

1. **Merge Selected PDFs (one step, right-click menu):** select 2+ PDFs →
   right-click → **Merge Selected PDFs** → a brief "Collecting selected
   PDFs…" window appears while the files are gathered, then the reorder dialog
   opens **once** with all of them (Up/Down sets page order, **Remove** drops
   a file) → **Merge**. Behind the scenes each selected file's invocation adds
   itself to a shared list and the first one (holding a lock that is held
   until the whole session ends) opens the dialog once — no matter how many
   files are selected, and later straggler processes never open a second
   dialog. Only files from the current selection count (timestamp filter), so
   leftovers from earlier sessions never sneak into the merge.
   **With a single PDF selected**, the same item acts as **add to the merge
   queue**: a confirmation pops up and the file lands in the queue — then
   finish with **Merge Queued PDFs** whenever you like. (The menu itself
   can't change per selection — the registry can't count selected files — so
   the verb adapts at runtime instead.)
2. **Queue for Merge / Merge Queued PDFs (right-click menu, explicit):**
   select PDFs → **Queue for Merge** (queues each) → **Merge Queued PDFs** →
   reorder dialog → **Merge**. Queue clears on success, stays if you Cancel
   so you can retry. Single-click "Merge Selected PDFs" also feeds this queue.
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

### Install — share one file
Cleanest for handing someone your app:

1. Run `python3 build_installer.py` in the repo → produces `dist/RightKitSetup.cmd`
   (re-run it after changing any packaged file).
2. Send the single file `RightKitSetup.cmd` to the user.
3. They **double-click it** → a console window shows "Extracting RightKit...",
   extracts to `%TEMP%`, then runs the normal install flow. That's the entire
   install — no extra steps for them.

Also works straight from a source checkout:
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
5. **Legacy cleanup** — deletes the old flat "Convert to PNG / JPEG / PDF"
   context-menu entries from the earlier scripts, which duplicated the
   submenu items (the old script files stay on disk; "Send to WSL" is
   untouched).
6. **Registry + shortcut** — imports `tools_menu.reg` (right-click submenu)
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
Explorer restart — setup asks before restarting). That puts RightKit Image and Pdf Tools
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
        │  MUIVerb "RightKit Image and Pdf Tools" + nested shell\NN_<verb>\command keys
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
- Menu items are grouped with **separator lines**: a verb key with
  `"CommandFlags"=dword:00000020` draws a line *above* that item (Explorer
  honours this inside a `SubCommands=""` cascade). The first item of each
  group after the first carries it, so the PDF menu reads merge / convert /
  split / compress / contact and the image menu reads convert / resize /
  contact. Grouping is by the numeric key prefix (`NN_…` sorts alphabetically).
- The **Contact Developer** verb is the one entry that doesn't go through
  Python — its command is `rundll32 url.dll,FileProtocolHandler <url>`, which
  opens the links page in the default browser.
- `setup.ps1` deletes the whole old `ImagePdfTools\shell` tree (HKCU + HKLM)
  **before** importing the `.reg`, so renamed/removed verbs can't linger as
  duplicates. `remove_duplicate_png.reg` does just the PNG-verb cleanup for a
  quick fix without rerunning the full installer.
- **Merging from multi-select** works despite Explorer firing the verb once
  per file: `Merge Selected PDFs` invocations append their file to a shared
  list in `%LOCALAPPDATA%\ImagePdfTools` and the first invocation to win an
  exclusive lock file collects the rest (`wait_queue_stable`: the list must
  stop changing for 1.2s, max 8s), then opens the dialog once. The lock is
  held until the session ends so no straggler can open a second dialog; the
  list is wiped at session end either way. Sibling writes are append-only
  (`O_APPEND`) so concurrent invocations can't erase each other's file, and
  a lock left by a crashed process is stolen after 15 minutes.

### 3.2 Files (in the `ImagePdfTools/` folder; deployed copies live in `C:\Scripts\imagepdf`)

| File                                    | Responsibility                               |
|-----------------------------------------|----------------------------------------------|
| `tools_common.py`                       | `unique_path()`, merge queue + lock helpers  |
| `image_tools.py`                        | image conversions + resizes                  |
| `pdf_tools.py`                          | PDF merge / split / compress / to-images     |
| `dialogs.py`                            | the tiny Tkinter dialogs (✕, drag, Cancel)   |
| `main.py` + `main.pyw`                  | action router + windowless entry point       |
| `tools.py`                              | namespace re-export (test seam)              |
| `tools_menu.reg`, `uninstall_tools.reg` | registry add / remove                        |
| `setup.ps1`, `setup.bat`                | one-click install (+ double-click wrapper)   |
| `remove_duplicate_png.reg`              | one-double-click fix for the old duplicate PNG verb |
| `uninstall.ps1`, `uninstall.bat`        | one-step uninstall (+ double-click wrapper)  |
| `restore_default_menu.bat`              | revert Win11 to the compact default menu     |

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
this path must change). One image per page, `_1`, `_2`… suffixes on
multi-page. **PNG** (default) for lossless pages; the **JPG** variant
flattens each page to RGB and saves at quality 90 — JPG is the right choice
for photo/scanned pages (≈7× smaller in tests) but *larger* than PNG for
dense screenshot pages, where PNG's lossless compression wins.

**Split** — `pypdf` reads the page count, then each output writer copies a
page range. Every-page: `file_1.pdf`…; every-N: ranges `1-3`, `4-6`, `7-7`
(last chunk may be smaller).

**Merge** — `pypdf.PdfWriter.append()` for each file in the order you set in
the reorder dialog → `merged.pdf`. The multi-select "Merge Selected PDFs"
mechanics (per-file firing, queue + lock) are described in section 3.1.

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
- **reorder_dialog** — listbox + Up/Down/**Remove** + Merge/Cancel for the
  merge order. Selection is re-set after moves/removals (Tk's `selection_set`
  proved additive in this build); removing everything makes Merge act as
  Cancel. Drag-to-move and a ✕ close button come from the shared base window.
- **progress_window** — a "Working…" label refreshed from the long-running
  task (the repaint is also what keeps the window alive during synchronous
  work); closing it early is safe — the task keeps running silently.

### 3.5 Error handling

`main.dispatch` wraps everything in a try/except that shows the error in a Tk
message box — important because `pyw.exe` has no console, so an unhandled
crash would otherwise fail silently. Cancelled dialogs and bad input never
write files.

---

## 4. Testing

50 automated tests (`python3 -m pytest`, all passing) cover the pure logic:
collision naming, resize binary search + best-effort floor, split chunking,
compress early-return + full search ladder, merge order, the router's action
table (dialog cancellation aborting, unknown actions, merge needing ≥ 2
files), and the merge-selected concurrency model (queue roundtrip, lock
exclusivity + stale-lock stealing, queue stability/min-len waiting, and a
5-thread race proving the dialog opens exactly once with all files). The GUI
dialogs were verified interactively (✕, drag, Cancel, Remove); Windows-side
behavior (registry, Send To, installer) is read-verified only — the first
real run on Windows is the final test. Multi-process burst behavior was
additionally verified with real concurrent-process simulations on Linux.

## 5. Known limits

- PDF compress is lossy (rasterized pages).
- Size targets are ceilings, not exact values.
- Merge-selected: if Explorer launches the per-file processes more than ~1.2s
  apart (e.g. extreme anti-virus delays), the burst can split into two
  dialogs; a sibling arriving while the dialog is already open is silently
  dropped from that merge. With a single PDF selected the click waits up to 8s
  (collecting possible siblings) before acting as "add to the merge queue".
- Merge accepts whatever files you send (it doesn't filter by extension);
  a non-PDF will surface an error box.
- Poppler path is hardcoded; moving `C:\poppler` requires updating
  `pdf_tools.py` (`POPLER`).
- The cascaded submenu uses the common-but-semi-documented `SubCommands=""`
  pattern; if the submenu appears empty on your Windows build, the parent
  key needs `ExtendedSubCommandsKey` instead (one-line registry change).

## 6. Future improvements

See **`features.md`** for the suggested-features backlog (prioritized, with
rationale and rough effort per item).
