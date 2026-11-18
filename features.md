# Image & PDF Tools — Suggested Features (backlog)

Ideas for future versions, prioritized. Priority reflects user value vs.
effort given the current architecture (queue/lock trick, per-file verb
firing, Tkinter dialogs). Each item lists where the work would land.

## High priority (biggest value, reasonable effort)

| # | Feature | Why | Where | Effort |
|---|---------|-----|-------|--------|
| 1 | **Multi-image → one PDF** — select several images → right-click → merge into a single multi-page PDF (same queue/lock trick as Merge Selected PDFs, but `to_pdf` appends pages instead of files) | The #1 gap: converting a scan batch into one document is the most common image+PDF workflow | `image_tools.py` (`to_pdf_multi`), `main.py` action, 1 reg verb under `image` | M |
| 2 | **Open output folder after long actions** — after compress/split/merge finishes, a "Done — Show files" button (or auto-open Explorer) so results are obvious | Slow operations currently end silently; users wonder if it worked | `main.py` `_progress` → after completion show a small done-dialog with a Show button (`explorer /select,<file>`) | S |
| 3 | **Cancel button that actually cancels** — long ops (compress 1–2 min) currently keep running after the window closes; a real cancel flag checked between render/encode steps | Users close the window expecting the work to stop | `dialogs.progress_window` → `.cancelled` flag; `pdf_tools.compress_to_kb` checks it per attempt | S–M |
| 4 | **JPG option for PDF→Images** — menu item "Convert to Images (JPG)" alongside PNG | PNG of photo pages is huge; JPG pages are ~10× smaller | `pdf_tools.to_images(fmt=...)`, 1 reg verb | S |
| 5 | **Remember dialog positions & last values** — save last window pos + last custom KB / N values to `%LOCALAPPDATA%\ImagePdfTools\settings.json`, prefill next time | Repeated workflows (always 100 KB, always split by 3) shouldn't need retyping | `tools_common` tiny load/save, `dialogs` prefill | S |

## Medium priority

| # | Feature | Why | Where | Effort |
|---|---------|-----|-------|--------|
| 6 | **Page range pick for split/compress** — optional "pages 3–8 only" field in the split-N dialog | Users rarely want all pages processed | `pypdf` already supports ranges; dialog + plumbing | M |
| 7 | **Rotate images / PDF pages** — 90° CW/CCW menu items | Common fix for scanned documents | `Pillow transpose`, `pypdf` page rotation; 2 verbs each | S |
| 8 | **Drag-and-drop reorder in the merge dialog** — listbox drag in addition to Up/Down | Feels natural with many files | `dialogs.reorder_dialog` (Tk listbox DnD is manual but well-known) | M |
| 9 | **Real progress bar** — percent done during compress (attempts are known in advance, so the bar can be estimated) | "Working…" label can't show how long is left | `dialogs.progress_window` + attempt counting in `compress_to_kb` | S |
| 10 | **Batch mode for image verbs** — "Resize All Selected…" using the same queue/lock collect-then-process pattern as merge | Resizing 20 photos one-by-one is painful | `main.py` new action reusing `MERGE_QUEUE_FILE`-style collect | M |
| 11 | **PDF password protect / remove password** — two small verbs | Security-adjacent, frequently requested | `pypdf` encrypt/decrypt; 2 verbs | S |
| 12 | **PDF metadata editor** — set title/author/strip metadata | Privacy when sharing PDFs | `pypdf` writer metadata; 1 verb + dialog | S |

## Low priority / ideas

| # | Feature | Why | Where | Effort |
|---|---------|-----|-------|--------|
| 13 | **Compress quality preview** — after choosing target, show achieved size vs. dpi before writing (or a tiny before/after preview image) | Confidence in what "98 KB at 50 dpi" looks like | `pdf_tools` + `dialogs` | M–L |
| 14 | **Watermark images/PDFs** — text or image overlay with opacity | Branding/stamping use case | `Pillow`, `reportlab`+pypdf overlay; new dep for PDF text watermark | M |
| 15 | **HEIC/HEIF input support** — iPhone photos straight to PDF/JPG | iPhone default format needs `pillow-heif` | 1 pip dep in `setup.ps1` + register in `image_tools` | S (code), adds dependency |
| 16 | **Per-format verb registration** — currently `image` covers all image types; narrow entries for `.jpg/.png/.webp` so the menu only shows relevant actions | Cleaner menu | `tools_menu.reg` key split | S |
| 17 | **OCR (searchable PDF from images)** — convert scanned PDFs into text-searchable ones | Powerful but heavyweight (tesseract dep, slow) | `pytesseract` + deps; L effort, new runtime dependency | L |
| 18 | **Dark mode dialogs** | Minor polish | `dialogs._base_window` colors | S |
| 19 | **Auto-update check** — setup writes a version file; context menu shows "Check for updates" comparing with a release URL | Only useful if updates are distributed somewhere reachable | `setup.ps1`, new verb | M |

## Not planned (deliberately)

- **Real shell extension DLL** (native multi-select merge without the queue
  trick): needs C++/COM registration and defeats the no-install-footprint
  goal; the queue/lock approach already delivers the same UX.
- **GUI main window**: the no-app-window constraint is a feature.

---
Maintenance note: when a feature lands, move its row out of here into the
README (usage + internals sections) and bump the test count.
