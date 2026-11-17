# Image & PDF Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Right-click "Image & PDF Tools" submenu on Windows exposing image→PDF/PNG/JPG, KB/pixel resizes, PDF→images, split, compress, plus Send-To multi-PDF merge with a reorder dialog.

**Architecture:** Pure-logic core (image_tools, pdf_tools, tools_common) imported by a thin `main.pyw` router that the registry verbs call with `pyw.exe`. Dialogs (custom value, pixel size, reorder) are tiny Tkinter windows shown only when the chosen verb needs input. Registry `.reg` files install the submenu; `install.ps1` wires deps, registry, and the Send To shortcut.

**Tech Stack:** Python 3 (pyw.exe), Pillow, img2pdf, pdf2image (+ poppler at `C:\poppler\poppler-24.08.0\Library\bin`), pypdf (new), Tkinter, Windows registry.

**Spec:** `docs/2026-11-17-image-pdf-tools-design.md`

## Global Constraints

- Outputs saved next to input; never overwrite input; collision → `_1`, `_2` suffix (design).
- `poppler_path=r"C:\poppler\poppler-24.08.0\Library\bin"` for pdf2image (verbatim, existing scripts).
- PDF compress/split/merge must not lose the source file; target KB sizes are ceilings.
- Scripts installed at `C:\Scripts\imagepdf\`; verbs invoke `pyw.exe "<path>\main.pyw" <action> "%1"`.
- Logic modules must be importable on Linux (no Windows-only code at import time) so tests run here.

## Review Focus

1. Output filename collision with existing file → expect `_1` suffix, never overwrite (test in Task 1).
2. Resize-to-KB when even quality 1 exceeds target → expect best-effort smallest file, no crash (test in Task 2).
3. Split every N where page count isn't divisible by N → expect last chunk smaller, all pages covered (test in Task 3).
4. Compress loop when input is already under target → expect no re-encode, copy path returned (test in Task 3).
5. Reorder dialog Cancel → expect merge aborts, no output file (manual check, Task 4).

---

### Task 1: Core helpers (`tools_common.py`)

**Files:**
- Create: `tools_common.py` (project root; deployed to `C:\Scripts\imagepdf\`)
- Test: `test_tools_common.py`

**Interfaces:**
- Produces: `unique_path(path: str) -> str` — if `path` exists, returns `base_1.ext`, `base_2.ext`, … first free variant; else `path` unchanged.

- [ ] **Step 1: Write failing tests** — `unique_path` returns input when absent; returns `_1` when present; skips to `_2` when `_1` also present.

- [ ] **Step 2: Run tests, expect FAIL** — `python -m pytest test_tools_common.py -v`

- [ ] **Step 3: Implement `unique_path`** (os.path.splitext loop).

- [ ] **Step 4: Run tests, expect PASS**

- [ ] **Step 5: Commit** `feat: unique output path helper`

### Task 2: Image tools (`image_tools.py`)

**Files:**
- Create: `image_tools.py`
- Test: `test_image_tools.py`

**Interfaces:**
- Consumes: `unique_path` (Task 1).
- Produces:
  - `to_pdf(src: str) -> str` — img2pdf to `<base>.pdf`
  - `to_png(src: str) -> str` / `to_jpg(src: str) -> str` — Pillow convert
  - `resize_to_kb(src: str, target_kb: int, encode=None) -> str` — `encode(img, quality) -> bytes` injectable for tests; default JPEG-encodes quality 95→1 via binary search on byte length ≤ `target_kb*1024`; writes first fit, else smallest attempt
  - `resize_to_pixels(src: str, width: int, height: int) -> str` — fit inside W×H preserving aspect ratio, PNG→PNG else JPEG q90 (my call: aspect preserved, no stretch)

- [ ] **Step 1: Write failing tests** — resize_to_kb with fake `encode` returning sizes 3000/1000/3000 for qualities (95, mid, 1…) hits ≤1024 bytes; pixel resize preserves aspect on 100×50 image to box 50×50 → 50×25; to_jpg on PNG input yields `.jpg` path.
- [ ] **Step 2: Run tests, expect FAIL**
- [ ] **Step 3: Implement** the four functions.
- [ ] **Step 4: Run tests, expect PASS**
- [ ] **Step 5: Commit** `feat: image conversions and resizes`

### Task 3: PDF tools (`pdf_tools.py`)

**Files:**
- Create: `pdf_tools.py`
- Test: `test_pdf_tools.py`

**Interfaces:**
- Consumes: `unique_path` (Task 1).
- Produces:
  - `merge(paths: list[str], out: str | None = None) -> str` — pypdf PdfWriter, default out `<dir>/merged.pdf`
  - `split_every_page(src: str) -> list[str]` — `<base>_1.pdf`, `_2.pdf`, … via pypdf
  - `split_every_n(src: str, n: int) -> list[str]` — uses `_chunks(total, n) -> list[tuple[int,int]]` (page ranges)
  - `compress_to_kb(src: str, target_kb: int, rasterize=None) -> str` — `rasterize(src, dpi, quality) -> bytes` injectable; if input size already ≤ target return src; else try dpi 150→72 with JPEG quality 80→40, rebuild via pypdf from images, first fit ≤ target wins, else best effort
  - `to_images(src: str) -> list[str]` — pdf2image dpi 200, PNG pages, poppler_path per Global Constraints

- [ ] **Step 1: Write failing tests** — `_chunks(7,3)` == `[(1,3),(4,6),(7,7)]`; compress with fake rasterize returning 4000 then 900 bytes and fake builder stops at second call and returns path; merge on real tiny PDFs made via pypdf writes a 2-page output.
- [ ] **Step 2: Run tests, expect FAIL**
- [ ] **Step 3: Implement** the functions.
- [ ] **Step 4: Run tests, expect PASS**
- [ ] **Step 5: Commit** `feat: pdf merge, split, compress, to-images`

### Task 4: Dialogs (`dialogs.py`)

**Files:**
- Create: `dialogs.py`

**Interfaces:**
- Produces:
  - `ask_value(title: str, label: str) -> str | None` — borderless Tk window, one Entry, Enter=OK (returns str), Esc/close=None
  - `ask_pixel_size() -> tuple[int, int] | None` — same window, "W x H" parse, invalid keeps window open
  - `reorder_dialog(paths: list[str]) -> list[str] | None` — Listbox + Up/Down buttons + Merge/Cancel; returns reordered list or None

No automated tests (GUI); manual check step only.

- [ ] **Step 1: Implement** the three dialogs (one small file).
- [ ] **Step 2: Manual check** on Linux with `python -c "from dialogs import *; print(ask_value('t','x'))"` and `reorder_dialog(['a.pdf','b.pdf'])` — verify Enter/Esc/Up/Down/Cancel behave per spec.
- [ ] **Step 3: Commit** `feat: input and reorder dialogs`

### Task 5: Router (`main.pyw`)

**Files:**
- Create: `main.pyw`
- Test: `test_main.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `dispatch(argv: list[str]) -> None` — argv like `["to-pdf", "img.jpg"]` or `["merge", "a.pdf", "b.pdf"]`; maps actions: `to-pdf, to-png, to-jpg, resize-kb-50/100/150/300, resize-kb-custom, resize-pixels, pdf-to-images, split-page, split-n, compress-100/500/1024/2048, compress-custom, merge`. Custom actions pull the value from the matching dialog; merge shows reorder dialog first; errors shown via Tk message box, never a traceback window (pyw has no console).

- [ ] **Step 1: Write failing test** — fake-injected `sys.argv` / monkeypatched dialog returns: `["resize-kb-custom", "x.jpg"]` with dialog returning "100" calls `resize_to_kb(src, 100)`; `["merge","a.pdf","b.pdf"]` with reorder returning `["b.pdf","a.pdf"]` calls `merge` in that order; unknown action shows error, no crash.
- [ ] **Step 2: Run tests, expect FAIL**
- [ ] **Step 3: Implement** dispatch table + `if __name__ == "__main__": dispatch(sys.argv[1:])`.
- [ ] **Step 4: Run all tests, expect PASS**
- [ ] **Step 5: Commit** `feat: action router entry point`

### Task 6: Windows wiring (registry + install)

**Files:**
- Create: `tools_menu.reg`, `install.ps1`, `uninstall_tools.reg`

**Interfaces:**
- Consumes: deployed `C:\Scripts\imagepdf\main.pyw` action names (Task 5).

- [ ] **Step 1: Write `tools_menu.reg`** — parent `MUIVerb`="Image & PDF Tools" under `SystemFileAssociations\image\shell` and `SystemFileAssociations\.pdf\shell`, nested `shell\NN_<verb>` keys whose commands run `pyw.exe "C:\Scripts\imagepdf\main.pyw" <action> "%1"`; image verbs only under `image`, pdf verbs only under `.pdf`.
- [ ] **Step 2: Write `install.ps1`** — copies project scripts to `C:\Scripts\imagepdf\`, `pip install pypdf`, `reg import tools_menu.reg`, creates Send To shortcut "Merge PDFs" → `pyw.exe C:\Scripts\imagepdf\main.pyw merge` (WScript.Shell), prints done.
- [ ] **Step 3: Write `uninstall_tools.reg`** — deletes the two parent shell keys (reg delete `-` syntax).
- [ ] **Step 4: Sanity check** — grep every action string in `.reg` exists in `main.pyw`'s dispatch table (scripted check).
- [ ] **Step 5: Commit** `feat: registry menu, installer, uninstaller`

---

## Deployment note (user-facing, not a task)

User runs `install.ps1` on Windows once; right-click any image/PDF → "Image & PDF Tools", and Send To → "Merge PDFs" for merge.
