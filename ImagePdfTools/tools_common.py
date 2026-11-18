import os

QUEUE_FILE = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                          "ImagePdfTools", "merge_queue.txt")


def queue_add(path):
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    existing = queue_read()
    if path not in existing:
        existing.append(path)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(existing))


def queue_read():
    try:
        with open(QUEUE_FILE, encoding="utf-8") as f:
            return [line for line in f.read().splitlines() if line]
    except FileNotFoundError:
        return []


def queue_clear():
    try:
        os.remove(QUEUE_FILE)
    except FileNotFoundError:
        pass


def unique_path(path):
    """Return a non-existing path: appends _1, _2, ... before the extension."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    return f"{base}_{i}{ext}"
