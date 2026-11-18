import os
import pypdf
import pdf_tools


def make_pdf(tmp_path, pages, name="a.pdf"):
    writer = pypdf.PdfWriter()
    for i in range(pages):
        writer.add_blank_page(width=72, height=72)
    p = tmp_path / name
    with open(p, "wb") as f:
        writer.write(f)
    return str(p)


def page_count(path):
    return len(pypdf.PdfReader(path).pages)


def test_chunks():
    assert pdf_tools._chunks(7, 3) == [(1, 3), (4, 6), (7, 7)]


def test_chunks_exact():
    assert pdf_tools._chunks(6, 3) == [(1, 3), (4, 6)]


def test_merge_two_pdfs(tmp_path):
    a = make_pdf(tmp_path, 2, "a.pdf")
    b = make_pdf(tmp_path, 1, "b.pdf")
    out = pdf_tools.merge([a, b])
    assert os.path.basename(out) == "merged.pdf"
    assert page_count(out) == 3


def test_merge_never_overwrites_existing_merged(tmp_path):
    a = make_pdf(tmp_path, 1, "a.pdf")
    b = make_pdf(tmp_path, 1, "b.pdf")
    pdf_tools.merge([a, b])
    out = pdf_tools.merge([a, b])
    assert os.path.basename(out) == "merged_1.pdf"


def test_split_every_page(tmp_path):
    src = make_pdf(tmp_path, 3)
    outs = pdf_tools.split_every_page(src)
    assert [page_count(o) for o in outs] == [1, 1, 1]
    assert [os.path.basename(o) for o in outs] == ["a_1.pdf", "a_2.pdf", "a_3.pdf"]


def test_split_every_n(tmp_path):
    src = make_pdf(tmp_path, 7)
    outs = pdf_tools.split_every_n(src, 3)
    assert [page_count(o) for o in outs] == [3, 3, 1]


def test_compress_already_small_returns_src(tmp_path):
    src = make_pdf(tmp_path, 1)

    def render(s, dpi):
        raise AssertionError("must not render")

    assert pdf_tools.compress_to_kb(src, 100, render=render) == src


def test_compress_picks_highest_quality_under_target(tmp_path):
    src = make_pdf(tmp_path, 10)
    calls = []

    def render(s, dpi):
        calls.append(dpi)
        return ["page"]  # fake pages

    def encode(page, quality):
        # monotonic: quality >= 48 -> too big (4000 B), below -> fits (900 B)
        return b"x" * (4000 if quality >= 48 else 900)

    def build(jpgs):
        return b"".join(jpgs)

    out = pdf_tools.compress_to_kb(src, 1, render=render, encode=encode, build=build)
    assert len(open(out, "rb").read()) == 900
    assert calls == [200]  # first dpi fits; never renders lower dpi


def test_compress_moves_to_lower_dpi_when_needed(tmp_path):
    src = make_pdf(tmp_path, 10)
    renders = []

    def render(s, dpi):
        renders.append(dpi)
        return ["page"]

    def encode(page, quality):
        # 200 dpi can never fit; 150 dpi fits below quality 48
        return b"x" * (8000 if dpi_of(render, renders[-1]) == 200 else
                       (4000 if quality >= 48 else 900))

    def dpi_of(render, last):
        return last

    def build(jpgs):
        return b"".join(jpgs)

    out = pdf_tools.compress_to_kb(src, 1, render=render, encode=encode, build=build)
    assert len(open(out, "rb").read()) == 900
    assert renders[:2] == [200, 150] and 110 not in renders  # stopped when 150 fit


def test_compress_best_effort_when_nothing_fits(tmp_path):
    src = make_pdf(tmp_path, 10)
    renders = []

    def render(s, dpi):
        renders.append(dpi)
        return ["page"]

    def encode(page, quality):
        # smaller dpi -> smaller output, but nothing under 1 KB
        sizes = {200: 99999, 150: 5000, 110: 2500, 72: 1200}
        return b"x" * sizes[renders[-1]]

    def build(jpgs):
        return b"".join(jpgs)

    out = pdf_tools.compress_to_kb(src, 1, render=render, encode=encode, build=build)
    assert len(open(out, "rb").read()) == 1200  # smallest attempt wins
    assert renders == [200, 150, 110, 72]
