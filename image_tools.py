import os
from io import BytesIO

from PIL import Image
import img2pdf

import tools_common


def _save(img, src, ext, fmt, **kwargs):
    out = tools_common.unique_path(os.path.splitext(src)[0] + ext)
    img.save(out, **kwargs)
    return out


def to_pdf(src):
    out = tools_common.unique_path(os.path.splitext(src)[0] + ".pdf")
    with open(out, "wb") as f:
        f.write(img2pdf.convert(src))
    return out


def to_png(src):
    return _save(Image.open(src).convert("RGBA"), src, ".png", "PNG")


def to_jpg(src):
    img = Image.open(src).convert("RGB")
    return _save(img, src, ".jpg", "JPEG", quality=90)


def _encode_jpeg(img, quality):
    buf = BytesIO()
    img.save(buf, "JPEG", quality=quality)
    return buf.getvalue()


def resize_to_kb(src, target_kb, encode=_encode_jpeg):
    """Shrink to <= target_kb via binary search on JPEG quality; best effort."""
    img = Image.open(src).convert("RGB")
    target = target_kb * 1024
    data = encode(img, 95)
    best = data
    lo, hi = 1, 95
    while lo < hi:
        mid = (lo + hi) // 2
        data = encode(img, mid)
        if len(data) <= target:
            best = data
            lo = mid + 1
        else:
            hi = mid
    out = tools_common.unique_path(os.path.splitext(src)[0] + ".jpg")
    with open(out, "wb") as f:
        f.write(best)
    return out


def resize_to_pixels(src, width, height):
    img = Image.open(src)
    img.thumbnail((width, height))  # fit inside box, aspect preserved
    ext = ".png" if src.lower().endswith(".png") else ".jpg"
    kwargs = {"PNG": {}} if ext == ".png" else {"JPEG": {"quality": 90}}
    fmt, opts = next(iter(kwargs.items()))
    return _save(img, src, ext, fmt, **opts)
