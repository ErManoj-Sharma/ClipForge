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


def _default_render(src, dpi):
    return convert_from_path(src, dpi=dpi, poppler_path=POPLER)


def _default_encode(page, quality):
    buf = BytesIO()
    page.convert("RGB").save(buf, "JPEG", quality=quality)
    return buf.getvalue()


def _default_build(jpg_blobs):
    return img2pdf.convert(jpg_blobs)


def compress_to_kb(src, target_kb, render=_default_render, encode=_default_encode,
                   build=_default_build, progress=None):
    """Rebuild the PDF from page images, maximizing quality under target_kb.

    For each dpi (high to low) a binary search finds the highest JPEG quality
    whose rebuilt size fits the target; the first dpi where anything fits wins,
    so output lands as close to the target as quality steps allow.
    """
    if os.path.getsize(src) <= target_kb * 1024:
        _report(progress, "Already under the target size - nothing to do")
        return src
    base = os.path.splitext(src)[0]
    target = target_kb * 1024
    fallback = None  # smallest attempt, used if nothing fits anywhere
    for dpi in (200, 150, 110, 72):
        _report(progress, f"Rendering pages at {dpi} dpi...")
        pages = render(src, dpi)
        best = None
        smallest = None
        lo, hi = 1, 95
        while lo <= hi:
            mid = (lo + hi) // 2
            _report(progress, f"{dpi} dpi: trying JPEG quality {mid}...")
            data = build([encode(p, mid) for p in pages])
            n = len(data)
            if n <= target:
                best = data
                lo = mid + 1
            else:
                if smallest is None or n < len(smallest):
                    smallest = data
                hi = mid - 1
        if best is not None:
            break
        if smallest is not None and (fallback is None or len(smallest) < len(fallback)):
            fallback = smallest
    out = tools_common.unique_path(f"{base}_compressed.pdf")
    with open(out, "wb") as f:
        f.write(best if best is not None else fallback)
    return out
