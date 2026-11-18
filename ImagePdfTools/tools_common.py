import os
import time

QUEUE_FILE = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                          "ImagePdfTools", "merge_queue.txt")
LOCK_FILE = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                         "ImagePdfTools", "merge.lock")
MERGE_QUEUE_FILE = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                                "ImagePdfTools", "merge_selected_queue.txt")


def queue_add(path, file=QUEUE_FILE):
    os.makedirs(os.path.dirname(file), exist_ok=True)
    # append instead of read-modify-write: Explorer fires siblings
    # simultaneously, so racing rewrites would silently drop files;
    # queue_read dedupes instead
    fd = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
    try:
        os.write(fd, (path + "\n").encode("utf-8"))
    finally:
        os.close(fd)


def queue_read(file=QUEUE_FILE):
    try:
        with open(file, encoding="utf-8") as f:
            lines = [line for line in f.read().splitlines() if line]
    except FileNotFoundError:
        return []
    seen, out = set(), []
    for p in lines:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def queue_clear(file=QUEUE_FILE):
    try:
        os.remove(file)
    except FileNotFoundError:
        pass


def _ensure_dirs():
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)


def acquire_lock(stale_after=900):
    """Exclusive claim for the one invocation that will show the merge dialog.
    Returns the lock path, or None if another invocation already owns it.
    A lock left behind by a crashed session (older than stale_after secs) is stolen."""
    _ensure_dirs()
    try:
        if time.time() - os.stat(LOCK_FILE).st_mtime > stale_after:
            os.remove(LOCK_FILE)
    except FileNotFoundError:
        pass
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


def wait_queue_stable(file=QUEUE_FILE, timeout=20.0, settle=1.2, poll=0.4,
                      min_len=0):
    """Wait until the queue file stops changing for `settle` seconds (all
    sibling invocations done queuing), then return its items. With min_len,
    keep waiting (up to `timeout`) until at least that many items are queued —
    covers siblings Explorer spawns late. Returns whatever is queued at the
    deadline."""
    deadline = time.time() + timeout
    last_sig = object()
    while True:
        try:
            st = os.stat(file)
            sig = (st.st_mtime_ns, st.st_size)
        except FileNotFoundError:
            sig = None
        items = queue_read(file)
        if sig == last_sig and len(items) >= min_len:
            return items
        last_sig = sig
        if time.time() >= deadline:
            return items
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
