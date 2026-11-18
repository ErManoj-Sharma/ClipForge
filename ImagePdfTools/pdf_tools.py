import os
from io import BytesIO

from PIL import Image
import img2pdf
import pypdf
from pdf2image import convert_from_path

import tools_common

POPLER = r"C:\poppler\poppler-24.08.0\Library\bin"


def _chunks(total, n):
    return [(s, min(s + n - 1, total)) for s in range(1, total + 1, n)]


def _report(progress, text):
    if progress:
        progress(text)


def merge(paths, out=None, progress=None):
    base = out or os.path.join(os.path.dirname(paths[0]), "merged.pdf")
    writer = pypdf.PdfWriter()
    for i, p in enumerate(paths):
        _report(progress, f"Adding {os.path.basename(p)} ({i + 1} of {len(paths)})...")
        writer.append(p)
    out = tools_common.unique_path(base)
    with open(out, "wb") as f:
        writer.write(f)
    return out


def _write_range(src, first, last, out):
    writer = pypdf.PdfWriter()
    for i in range(first - 1, last):
        writer.add_page(pypdf.PdfReader(src).pages[i])
    with open(out, "wb") as f:
        writer.write(f)
    return out


def split_every_page(src, progress=None):
    base = os.path.splitext(src)[0]
    total = len(pypdf.PdfReader(src).pages)
    outs = []
    for i in range(1, total + 1):
        _report(progress, f"Writing file {i} of {total}...")
        outs.append(_write_range(src, i, i, tools_common.unique_path(f"{base}_{i}.pdf")))
    return outs


def split_every_n(src, n, progress=None):
    base = os.path.splitext(src)[0]
    total = len(pypdf.PdfReader(src).pages)
    ranges = _chunks(total, n)
    outs = []
    for k, (a, b) in enumerate(ranges):
        _report(progress, f"Writing part {k + 1} of {len(ranges)} (pages {a}-{b})...")
        outs.append(_write_range(src, a, b, tools_common.unique_path(f"{base}_{a}-{b}.pdf")))
    return outs


def to_images(src, progress=None):
    base = os.path.splitext(src)[0]
    pages = convert_from_path(src, dpi=200, poppler_path=POPLER)
    outs = []
    for i, page in enumerate(pages):
        _report(progress, f"Saving page {i + 1} of {len(pages)}...")
        suffix = f"_{i + 1}" if len(pages) > 1 else ""
        out = tools_common.unique_path(f"{base}{suffix}.png")
        page.save(out, "PNG")
        outs.append(out)
    return outs


def _default_rasterize(src, dpi, quality):
    """Pages -> JPEG bytes of a rebuilt single PDF at given dpi/quality."""
    pages = convert_from_path(src, dpi=dpi, poppler_path=POPLER)
    jpgs = []
    for page in pages:
        buf = BytesIO()
        page.convert("RGB").save(buf, "JPEG", quality=quality)
        jpgs.append(buf.getvalue())
    return img2pdf.convert(jpgs)


def _default_build(pdf_bytes):
    buf = BytesIO(pdf_bytes)
    writer = pypdf.PdfWriter()
    writer.append(buf)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def compress_to_kb(src, target_kb, rasterize=_default_rasterize, build=_default_build, progress=None):
    """Rasterize at decreasing dpi/quality until the PDF fits target_kb (ceiling)."""
    if os.path.getsize(src) <= target_kb * 1024:
        _report(progress, "Already under the target size - nothing to do")
        return src
    base = os.path.splitext(src)[0]
    best = None
    ladder = ((150, 80), (110, 60), (72, 40))
    for i, (dpi, quality) in enumerate(ladder):
        _report(progress, f"Compressing: pass {i + 1} of {len(ladder)} ({dpi} dpi)...")
        data = build(rasterize(src, dpi, quality))
        if len(data) <= target_kb * 1024:
            best = data
            break
        best = data  # keep smallest attempt for best effort
    out = tools_common.unique_path(f"{base}_compressed.pdf")
    with open(out, "wb") as f:
        f.write(best)
    return out
