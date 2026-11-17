import sys, img2pdf, os
input_path = sys.argv[1]
output_path = os.path.splitext(input_path)[0] + ".pdf"
with open(output_path, "wb") as f:
    f.write(img2pdf.convert(input_path))
