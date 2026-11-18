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

    def rasterize(s, dpi, quality):
        raise AssertionError("must not rasterize")

    assert pdf_tools.compress_to_kb(src, 100, rasterize=rasterize) == src


def test_compress_stops_at_first_fit(tmp_path):
    src = make_pdf(tmp_path, 60)  # must be > 1KB so the early-return doesn't fire
    blobs = {(150, 80): b"x" * 4000, (110, 60): b"x" * 2000, (72, 40): b"x" * 900}
    calls = []

    def rasterize(s, dpi, quality):
        calls.append((dpi, quality))
        return blobs[(dpi, quality)]

    def build(pdf_bytes):
        return pdf_bytes  # contract: rebuild PDF bytes from rasterized pages

    out = pdf_tools.compress_to_kb(src, 1, rasterize=rasterize, build=build)
    assert len(open(out, "rb").read()) <= 1024
    assert calls == [(150, 80), (110, 60), (72, 40)]  # stopped as soon as it fit
