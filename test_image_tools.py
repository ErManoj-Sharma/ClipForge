import os

from PIL import Image
import image_tools


def make_img(tmp_path, name="a.png", size=(100, 50), color=(255, 0, 0)):
    p = tmp_path / name
    Image.new("RGB", size, color).save(p)
    return str(p)


def test_to_jpg_converts_png(tmp_path):
    src = make_img(tmp_path)
    out = image_tools.to_jpg(src)
    assert out.endswith(".jpg") and os.path.exists(out)
    assert Image.open(out).size == (100, 50)


def test_to_png(tmp_path):
    src = make_img(tmp_path, name="a.jpg")
    out = image_tools.to_png(src)
    assert out.endswith(".png") and os.path.exists(out)


def test_to_pdf(tmp_path):
    src = make_img(tmp_path)
    out = image_tools.to_pdf(src)
    assert out.endswith(".pdf") and os.path.exists(out)
    assert open(out, "rb").read(5) == b"%PDF-"


def test_resize_kb_hits_target_with_fake_encoder(tmp_path):
    src = make_img(tmp_path)
    # fake encoder: quality 95 -> 3000 bytes, 48 -> 1000 bytes, anything else -> 3000
    sizes = {95: 3000, 48: 1000, 24: 1000}
    calls = []

    def encode(img, quality):
        calls.append(quality)
        return b"x" * sizes.get(quality, 3000)

    out = image_tools.resize_to_kb(src, 1, encode=encode)  # target 1 KB = 1024 B
    assert len(open(out, "rb").read()) <= 1024
    assert calls  # encoder was used


def test_resize_kb_best_effort_when_floor_exceeds_target(tmp_path):
    src = make_img(tmp_path)

    def encode(img, quality):
        return b"x" * 9999  # always too big

    out = image_tools.resize_to_kb(src, 1, encode=encode)
    assert len(open(out, "rb").read()) == 9999  # smallest attempt still written


def test_resize_kb_best_effort_writes_smallest(tmp_path):
    src = make_img(tmp_path)

    def encode(img, quality):
        # monotonic: low quality -> small file, high quality -> big file
        return b"x" * (2000 if quality <= 5 else 5000)

    out = image_tools.resize_to_kb(src, 1, encode=encode)
    assert len(open(out, "rb").read()) == 2000  # smallest attempt, not q95's


def test_resize_pixels_preserves_aspect(tmp_path):
    src = make_img(tmp_path)
    out = image_tools.resize_to_pixels(src, 50, 50)
    assert Image.open(out).size == (50, 25)  # 100x50 fit inside 50x50


def test_never_overwrites_source(tmp_path):
    src = make_img(tmp_path, name="a.jpg")
    out = image_tools.to_png(src)
    assert out != src and os.path.exists(src)
