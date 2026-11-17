# Image & PDF Tools — right-click suite for Windows

## Intent
One tool exposing all conversions/resizes/merge/split/compress from the Explorer
right-click menu. No app window; a tiny dialog appears only when a "Custom…" value
is needed.

## Approach (picked by user: Option B — one submenu)
- Single parent entry **"Image & PDF Tools"** in the classic context menu,
  with cascaded submenus (registry `ExtendedSubCommandsKey`).
- **Merge PDFs** lives in the **Send To** menu: Send To passes all selected files
  to the command at once; ordinary context-menu verbs fire once per file.
- Scripts at `C:\Scripts\` (existing pattern), invoked via `pyw.exe` so no console
  window flashes.

## Menu structure

```
Image & PDF Tools ─┬─ Convert to PDF          (any image)
                   ├─ Convert to PNG          (image)
                   ├─ Convert to JPG          (image)
                   ├─ Resize to 50 KB
                   ├─ Resize to 100 KB
                   ├─ Resize to 150 KB
                   ├─ Resize to 300 KB
                   ├─ Resize to Custom KB…    (tiny dialog: KB value)
                   ├─ Resize to Pixel Size…   (tiny dialog: W x H)
                   └─ (PDF files:)
                      ├─ Convert to Images    (existing pdf2image behavior)
                      ├─ Split Every Page     (file.pdf → file_1.pdf, _2.pdf, …)
                      ├─ Split Every N Pages… (tiny dialog: N)
                      ├─ Compress to 100 KB
                      ├─ Compress to 500 KB
                      ├─ Compress to 1 MB
                      ├─ Compress to 2 MB
                      └─ Compress to Custom…  (tiny dialog: KB value)

Send To ── Merge PDFs   (multi-select PDFs → merged.pdf in same folder)
```

## Behavior details
- Output always saved next to the input; never overwrites the input file.
  Name collision → append `_1`, `_2`, …
- Custom dialog: borderless Tkinter window, one input, Enter = OK, Esc = close.
- Image resize-to-KB: binary search JPEG quality until size ≤ target (min
  quality floor). Works by converting to JPEG — PNG input stays PNG-named
  output? No: output is `.jpg` when target size requires JPEG compression.
- PDF compress: rasterize pages via pdf2image at decreasing DPI/JPEG quality
  until file ≤ target. Lossy (pages become images) — stated limitation.
- Split custom N: chunks of N pages; last chunk may be smaller.
- Merge: opens a small reorder dialog listing the selected PDFs with
  Up/Down buttons to set the sequence, then Merge/Cancel. (Explorer doesn't
  pass a guaranteed selection order, so the user sets the order explicitly.)

## Dependencies (install once)
- Already present: Pillow, img2pdf, pdf2image, poppler at
  `C:\poppler\poppler-24.08.0\Library\bin`
- New: `pypdf` (merge/split), `tkinter` (ships with Python)

## Non-goals
- No GUI app, no tray icon, no installer wizard.
- No lossless PDF compression guarantees (target is a ceiling, not exact size).

## Registry files (new, replacing/adding to existing)
- `tools_menu.reg` — the Image & PDF Tools submenu (image + PDF verbs).
- `merge_sendto.reg` + a `.lnk`/shortcut approach: a `Merge PDFs` shortcut in
  the user's SendTo folder pointing to the merge script.
- `uninstall_tools.reg` — removes everything the new files add.

## What's left to the builder
- Exact icon choices for submenu (can reuse existing .ico or none).
- Whether Convert to Images outputs PNG, JPG, or both (current: PNG script
  exists; JPG exists too — keep both as one entry "Convert to Images" → PNG,
  since JPG already exists as a preset elsewhere).
