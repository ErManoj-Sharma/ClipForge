"""Image & PDF Tools — action router.
Usage: pyw.exe main.pyw <action> <file> [file...]
"""
import sys
import traceback

import tools
import dialogs

RESIZE_KB = {"resize-kb-50": 50, "resize-kb-100": 100,
             "resize-kb-150": 150, "resize-kb-300": 300}
COMPRESS_KB = {"compress-100": 100, "compress-500": 500,
               "compress-1024": 1024, "compress-2048": 2048}


def show_error(msg):
    import tkinter.messagebox as mb
    mb.showerror("Image & PDF Tools", msg)


def _val(title, label):
    v = dialogs.ask_value(title, label)
    if v is None:
        return None
    try:
        return int(v)
    except ValueError:
        show_error(f"'{v}' is not a number")
        return None


def dispatch(argv):
    if not argv:
        show_error("No action given")
        return
    action, files = argv[0], argv[1:]
    try:
        if not files:
            show_error("No file selected")
            return
        src = files[0]
        if action in RESIZE_KB:
            tools.resize_to_kb(src, RESIZE_KB[action])
        elif action == "resize-kb-custom":
            kb = _val("Resize to Custom KB", "Target size in KB:")
            if kb is not None:
                tools.resize_to_kb(src, kb)
        elif action == "resize-pixels":
            size = dialogs.ask_pixel_size()
            if size is not None:
                tools.resize_to_pixels(src, *size)
        elif action == "to-pdf":
            tools.to_pdf(src)
        elif action == "to-png":
            tools.to_png(src)
        elif action == "to-jpg":
            tools.to_jpg(src)
        elif action == "pdf-to-images":
            tools.to_images(src)
        elif action == "split-page":
            tools.split_every_page(src)
        elif action == "split-n":
            n = _val("Split Every N Pages", "Pages per file:")
            if n is not None:
                if n < 1:
                    show_error("Pages per file must be at least 1")
                    return
                tools.split_every_n(src, n)
        elif action in COMPRESS_KB:
            tools.compress_to_kb(src, COMPRESS_KB[action])
        elif action == "compress-custom":
            kb = _val("Compress to Custom", "Target size in KB:")
            if kb is not None:
                tools.compress_to_kb(src, kb)
        elif action == "merge":
            if len(files) < 2:
                show_error("Select at least two PDFs to merge")
                return
            ordered = dialogs.reorder_dialog(sorted(files))
            if ordered is not None:
                tools.merge(ordered)
        else:
            show_error(f"Unknown action: {action}")
    except Exception:
        show_error("Something went wrong:\n" + traceback.format_exc())


if __name__ == "__main__":
    dispatch(sys.argv[1:])
