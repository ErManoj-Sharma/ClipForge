import sys, os
from PIL import Image
input_path = sys.argv[1]
output_path = os.path.splitext(input_path)[0] + ".png"
Image.open(input_path).save(output_path, "PNG")
