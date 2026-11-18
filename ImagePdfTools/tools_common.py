import os
import time

QUEUE_FILE = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                          "ImagePdfTools", "merge_queue.txt")
LOCK_FILE = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                         "ImagePdfTools", "merge.lock")


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


def _ensure_dirs():
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)


def acquire_lock():
    """Exclusive claim for the one invocation that will show the merge dialog.
    Returns the lock path, or None if another invocation already owns it."""
    _ensure_dirs()
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return LOCK_FILE
    except FileExistsError:
        return None


def release_lock(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def wait_queue_stable(timeout=20.0, settle=1.2, poll=0.4):
    """Wait until the queue file stops changing for `settle` seconds (all
    sibling invocations done queuing), then return its items. If the queue
    never settles within `timeout`, returns whatever is queued."""
    deadline = time.time() + timeout
    last_sig = object()
    while True:
        try:
            st = os.stat(QUEUE_FILE)
            sig = (st.st_mtime_ns, st.st_size)
        except FileNotFoundError:
            sig = None
        if sig == last_sig:
            return queue_read()
        last_sig = sig
        if time.time() >= deadline:
            return queue_read()
        time.sleep(poll)


def unique_path(path):
    """Return a non-existing path: appends _1, _2, ... before the extension."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(f"{base}_{i}{ext}"):
        i += 1
    return f"{base}_{i}{ext}"
