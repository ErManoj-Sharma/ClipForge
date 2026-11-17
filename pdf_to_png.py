import sys, os
from pdf2image import convert_from_path
pdf_path = sys.argv[1]
base = os.path.splitext(pdf_path)[0]
pages = convert_from_path(pdf_path, dpi=200, poppler_path=r"C:\poppler\poppler-24.08.0\Library\bin")
for i, page in enumerate(pages):
    suffix = f"_{i+1}" if len(pages) > 1 else ""
    page.save(f"{base}{suffix}.png", "PNG")
