"""RightKit Image and Pdf Tools — action router.
Usage: pyw.exe main.pyw <action> <file> [file...]
"""
import os
import sys
import time
import traceback

import tools
import dialogs
from tools_common import (queue_add, queue_read, queue_clear,
                          acquire_lock, release_lock, wait_queue_stable,
                          MERGE_QUEUE_FILE)

RESIZE_KB = {"resize-kb-50": 50, "resize-kb-100": 100,
             "resize-kb-150": 150, "resize-kb-300": 300}
COMPRESS_KB = {"compress-100": 100, "compress-500": 500,
               "compress-1024": 1024, "compress-2048": 2048}
VERSION_FILE = r"C:\Scripts\imagepdf\version.txt"
CURRENT_VERSION = "1.0.0"
UPDATE_MANIFEST_URL = ("https://raw.githubusercontent.com/"
                       "ErManoj-Sharma/ClipForge/master/dist/version.json")


def show_error(msg):
    import tkinter.messagebox as mb
    mb.showerror("RightKit Image and Pdf Tools", msg)


def show_info(msg):
    import tkinter.messagebox as mb
    mb.showinfo("RightKit Image and Pdf Tools", msg)


def _progress(title, fn, *args, **kwargs):
    """Run a slow tool with the 'Working...' window showing live steps."""
    p = dialogs.progress_window(title)
    try:
        fn(*args, progress=p, **kwargs)
    finally:
        p.close()


def _busy(title, fn, *args):
    """Run a fast tool with a plain 'Working...' window (no console flash)."""
    p = dialogs.progress_window(title)
    try:
        fn(*args)
    finally:
        p.close()


def _val(title, label):
    v = dialogs.ask_value(title, label)
    if v is None:
        return None
    try:
        return int(v)
    except ValueError:
        show_error(f"'{v}' is not a number")
        return None


def _merge_selected(src):
    """'Merge Selected PDFs': Explorer fires this verb once per selected file,
    so every invocation queues its file; the first one to win the lock watches
    the queue until the siblings finish, then opens the merge dialog once.
    The lock is held until the whole session ends (dialog included) so no
    straggler can open a second dialog. Only files queued during this burst
    count (timestamp filter), so leftovers from previous sessions never
    sneak into the merge. With a single selection nothing else arrives: the
    click then means "add to the merge queue" and 'Merge Queued PDFs'
    finishes the job."""
    burst_start = int(time.time()) - 2
    queue_add(src, file=MERGE_QUEUE_FILE, ts=burst_start)
    lock = acquire_lock()
    if lock is None:
        return  # a sibling invocation is already handling the dialog
    try:
        # visible feedback while waiting for the sibling invocations
        win = dialogs.progress_window("Collecting selected PDFs...")
        try:
            items = wait_queue_stable(file=MERGE_QUEUE_FILE, min_len=2,
                                      timeout=8, since=burst_start)
        finally:
            win.close()
        if len(items) < 2:
            # single selection: the click meant "add to the merge queue"
            queue_add(src)
            show_info("Added to the merge queue.\n\nSelect more PDFs and use "
                      "'Merge Selected PDFs', or right-click a PDF and use "
                      "'Merge Queued PDFs' to merge what's queued.")
            return
        ordered = dialogs.reorder_dialog(items)
        if ordered is not None:
            _progress("Merging PDFs...", tools.merge, ordered)
    finally:
        queue_clear(file=MERGE_QUEUE_FILE)
        release_lock(lock)


def _version_tuple(v):
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def _installed_version():
    try:
        with open(VERSION_FILE, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return CURRENT_VERSION


def _fetch_manifest():
    import json
    import urllib.request
    with urllib.request.urlopen(UPDATE_MANIFEST_URL, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def _download(url, path):
    import urllib.request
    with urllib.request.urlopen(url, timeout=30) as r:
        with open(path, "wb") as f:
            f.write(r.read())


def _open_installer(path):
    os.startfile(path)


def _ask_yes(title, msg):
    import tkinter.messagebox as mb
    return mb.askyesno(title, msg)


def check_update():
    """'Check for Update' — fetch the latest version manifest and, if newer
    than the installed one, download + run the new installer (the install
    itself runs setup.ps1, so the update completes on re-launch)."""
    try:
        m = _fetch_manifest()
    except Exception as e:
        show_error("Could not check for updates:\n" + str(e))
        return
    local = _installed_version()
    remote = str(m.get("version", "")).strip()
    if not remote or _version_tuple(remote) <= _version_tuple(local):
        show_info(f"RightKit is up to date (v{local}).")
        return
    url = str(m.get("installer", "")).strip()
    if not url:
        show_info(f"New version {remote} is available (no download URL).")
        return
    if not _ask_yes("Update available",
                    f"RightKit {remote} is available.\nDownload and update now?"):
        show_info(f"New version {remote} is available (not downloaded).")
        return
    tmp = os.path.join(os.environ.get("TEMP", r"C:\Windows\Temp"),
                       "RightKitSetup.cmd")
    try:
        _download(url, tmp)
    except Exception as e:
        show_error("Download failed:\n" + str(e))
        return
    _open_installer(tmp)
    show_info(f"RightKit {remote}: update initiated.\n"
              f"Run the installer when it opens (copy of: {tmp}).")


def dispatch(argv):
    if not argv:
        show_error("No action given")
        return
    action, files = argv[0], argv[1:]
    try:
        if action == "check-update":
            check_update()
            return
        if not files:
            show_error("No file selected")
            return
        src = files[0]
        if action in RESIZE_KB:
            _progress("Resizing image...", tools.resize_to_kb, src, RESIZE_KB[action])
        elif action == "resize-kb-custom":
            kb = _val("Resize to Custom KB", "Target size in KB:")
            if kb is not None:
                _progress("Resizing image...", tools.resize_to_kb, src, kb)
        elif action == "resize-pixels":
            size = dialogs.ask_pixel_size()
            if size is not None:
                _busy("Resizing image...", tools.resize_to_pixels, src, *size)
        elif action == "to-pdf":
            _busy("Converting to PDF...", tools.to_pdf, src)
        elif action == "to-png":
            _busy("Converting to PNG...", tools.to_png, src)
        elif action == "to-jpg":
            _busy("Converting to JPG...", tools.to_jpg, src)
        elif action == "pdf-to-images":
            _progress("Converting PDF to images...", tools.to_images, src)
        elif action == "pdf-to-images-jpg":
            _progress("Converting PDF to images...", tools.to_images, src,
                      fmt="JPEG")
        elif action == "split-page":
            _progress("Splitting PDF...", tools.split_every_page, src)
        elif action == "split-n":
            n = _val("Split Every N Pages", "Pages per file:")
            if n is not None:
                if n < 1:
                    show_error("Pages per file must be at least 1")
                    return
                _progress("Splitting PDF...", tools.split_every_n, src, n)
        elif action in COMPRESS_KB:
            _progress("Compressing PDF...", tools.compress_to_kb, src, COMPRESS_KB[action])
        elif action == "compress-custom":
            kb = _val("Compress to Custom", "Target size in KB:")
            if kb is not None:
                _progress("Compressing PDF...", tools.compress_to_kb, src, kb)
        elif action == "merge-selected":
            _merge_selected(src)
        elif action == "queue":
            queue_add(src)
        elif action == "merge-queue":
            items = queue_read()
            if len(items) < 2:
                show_error("Queue at least two PDFs first:\n"
                           "select them, right-click -> 'Queue for Merge',\n"
                           "then use 'Merge Queued PDFs'.")
                return
            ordered = dialogs.reorder_dialog(items)
            if ordered is not None:
                _progress("Merging PDFs...", tools.merge, ordered)
                queue_clear()
        elif action == "merge":
            if len(files) < 2:
                show_error("Select at least two PDFs to merge")
                return
            ordered = dialogs.reorder_dialog(sorted(files))
            if ordered is not None:
                _progress("Merging PDFs...", tools.merge, ordered)
        else:
            show_error(f"Unknown action: {action}")
    except Exception:
        show_error("Something went wrong:\n" + traceback.format_exc())


if __name__ == "__main__":
    dispatch(sys.argv[1:])
