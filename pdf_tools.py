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


def merge(paths, out=None):
    base = out or os.path.join(os.path.dirname(paths[0]), "merged.pdf")
    writer = pypdf.PdfWriter()
    for p in paths:
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


def split_every_page(src):
    base = os.path.splitext(src)[0]
    total = len(pypdf.PdfReader(src).pages)
    return [_write_range(src, i, i, tools_common.unique_path(f"{base}_{i}.pdf"))
            for i in range(1, total + 1)]


def split_every_n(src, n):
    base = os.path.splitext(src)[0]
    total = len(pypdf.PdfReader(src).pages)
    return [_write_range(src, a, b, tools_common.unique_path(f"{base}_{a}-{b}.pdf"))
            for a, b in _chunks(total, n)]


def to_images(src):
    base = os.path.splitext(src)[0]
    pages = convert_from_path(src, dpi=200, poppler_path=POPLER)
    outs = []
    for i, page in enumerate(pages):
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


def compress_to_kb(src, target_kb, rasterize=_default_rasterize, build=_default_build):
    """Rasterize at decreasing dpi/quality until the PDF fits target_kb (ceiling)."""
    if os.path.getsize(src) <= target_kb * 1024:
        return src
    base = os.path.splitext(src)[0]
    best = None
    for dpi, quality in ((150, 80), (110, 60), (72, 40)):
        data = build(rasterize(src, dpi, quality))
        if len(data) <= target_kb * 1024:
            best = data
            break
        best = data  # keep smallest attempt for best effort
    out = tools_common.unique_path(f"{base}_compressed.pdf")
    with open(out, "wb") as f:
        f.write(best)
    return out
