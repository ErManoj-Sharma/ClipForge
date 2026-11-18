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


def to_images(src, progress=None, fmt="PNG"):
    base = os.path.splitext(src)[0]
    jpg = fmt.upper() in ("JPEG", "JPG")
    pages = convert_from_path(src, dpi=200, poppler_path=POPLER)
    outs = []
    for i, page in enumerate(pages):
        _report(progress, f"Saving page {i + 1} of {len(pages)}...")
        suffix = f"_{i + 1}" if len(pages) > 1 else ""
        out = tools_common.unique_path(f"{base}{suffix}.{'jpg' if jpg else 'png'}")
        if jpg:
            # PDF pages can carry alpha; JPEG needs plain RGB
            page.convert("RGB").save(out, "JPEG", quality=90)
        else:
            page.save(out, "PNG")
        outs.append(out)
    return outs


def _default_render(src, dpi):
    return convert_from_path(src, dpi=dpi, poppler_path=POPLER)


def _default_encode(page, quality, gray=False):
    buf = BytesIO()
    page.convert("L" if gray else "RGB").save(buf, "JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def _default_encode_png(page, colors):
    buf = BytesIO()
    page.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT).save(
        buf, "PNG", optimize=True)
    return buf.getvalue()


def _default_build(jpg_blobs):
    return img2pdf.convert(jpg_blobs)


def _fit(pages, encode, build, target, label, progress, lo, hi):
    """Binary search encode params (monotonic size) for the largest result <=
    target. Returns the best bytes, or None plus the smallest missed attempt."""
    best = None
    smallest = None
    while lo <= hi:
        mid = (lo + hi) // 2
        _report(progress, f"{label} {mid}...")
        data = build([encode(p, mid) for p in pages])
        n = len(data)
        if n <= target:
            best = data
            lo = mid + 1
        else:
            if smallest is None or n < len(smallest):
                smallest = data
            hi = mid - 1
    return best, smallest


def compress_to_kb(src, target_kb, render=_default_render, encode=_default_encode,
                   encode_png=_default_encode_png, build=_default_build, progress=None):
    """Rebuild the PDF from page images, maximizing quality under target_kb.

    Search space per dpi (200 → 40): color JPEG, grayscale JPEG, palette PNG —
    each binary-searched for the largest result that fits the target. The first
    dpi where anything fits wins, so output lands just under the target at the
    best quality the space allows. Dense screenshots usually need grayscale or
    palette PNG; photos fit as color JPEG at high dpi.
    """
    if os.path.getsize(src) <= target_kb * 1024:
        _report(progress, "Already under the target size - nothing to do")
        return src
    base = os.path.splitext(src)[0]
    target = target_kb * 1024
    fallback = None  # smallest attempt overall, used if nothing fits anywhere

    def track(smallest):
        nonlocal fallback
        if smallest is not None and (fallback is None or len(smallest) < len(fallback)):
            fallback = smallest

    for dpi in (200, 150, 110, 72, 50, 40):
        _report(progress, f"Rendering pages at {dpi} dpi...")
        pages = render(src, dpi)
        # 1) color JPEG quality 95..1
        best, smallest = _fit(pages, lambda p, q: encode(p, q, gray=False), build,
                              target, f"{dpi} dpi: color JPEG quality", progress, 1, 95)
        track(smallest)
        if best is None:
            # 2) grayscale JPEG quality 95..1
            best, smallest = _fit(pages, lambda p, q: encode(p, q, gray=True), build,
                                  target, f"{dpi} dpi: grayscale JPEG quality", progress, 1, 95)
            track(smallest)
        if best is None:
            # 3) palette PNG colors 256..4
            best, smallest = _fit(pages, lambda p, c: encode_png(p, c), build,
                                  target, f"{dpi} dpi: PNG colors", progress, 4, 256)
            track(smallest)
        if best is not None:
            break
    out = tools_common.unique_path(f"{base}_compressed.pdf")
    with open(out, "wb") as f:
        f.write(best if best is not None else fallback)
    return out
