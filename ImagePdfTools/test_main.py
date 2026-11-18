import sys
import os
import tools_common
import main as main_mod


class FakeProgress:
    def __init__(self):
        self.texts = []
        self.closed = False

    def __call__(self, text):
        self.texts.append(text)

    def close(self):
        self.closed = True


def run(monkeypatch, argv, queue=None, **overrides):
    """Call dispatch with patched deps; returns kwargs of the called tool fn."""
    calls = {}

    def capture(name):
        def fn(*args, **kwargs):
            calls[name] = (args, kwargs)
            return "out/path"
        return fn

    for name in ("to_pdf", "to_png", "to_jpg", "resize_to_kb", "resize_to_pixels",
                 "merge", "split_every_page", "split_every_n",
                 "compress_to_kb", "to_images"):
        monkeypatch.setattr(main_mod.tools, name, capture(name), raising=False)
    for mod_name, attr in overrides.items():
        monkeypatch.setattr(main_mod, mod_name, attr)
    monkeypatch.setattr(main_mod, "show_error", lambda *a: calls.setdefault("error", a))
    prog = FakeProgress()
    monkeypatch.setattr(main_mod.dialogs, "progress_window", lambda title: prog, raising=False)
    # queue helpers: recorded in-memory instead of a real file
    monkeypatch.setattr(main_mod, "queue_read", lambda *a, **k: list(queue or []), raising=False)
    monkeypatch.setattr(main_mod, "queue_add", lambda p, **k: calls.setdefault("_queue", []).append(p), raising=False)
    monkeypatch.setattr(main_mod, "queue_clear", lambda **k: calls.setdefault("_queue_cleared", True), raising=False)
    main_mod.dispatch(argv)
    calls["_progress"] = prog
    return calls


def test_preset_resize_kb(monkeypatch):
    calls = run(monkeypatch, ["resize-kb-100", "a.jpg"])
    assert calls["resize_to_kb"][0] == ("a.jpg", 100)
    assert calls["resize_to_kb"][1].get("progress") is calls["_progress"]


def test_custom_resize_uses_dialog(monkeypatch):
    monkeypatch.setattr(main_mod.dialogs, "ask_value", lambda t, l: "150")
    calls = run(monkeypatch, ["resize-kb-custom", "a.jpg"])
    assert calls["resize_to_kb"][0] == ("a.jpg", 150)


def test_custom_resize_cancelled_shows_nothing(monkeypatch):
    monkeypatch.setattr(main_mod.dialogs, "ask_value", lambda t, l: None)
    calls = run(monkeypatch, ["resize-kb-custom", "a.jpg"])
    assert "resize_to_kb" not in calls


def test_resize_pixels(monkeypatch):
    monkeypatch.setattr(main_mod.dialogs, "ask_pixel_size", lambda: (800, 600))
    calls = run(monkeypatch, ["resize-pixels", "a.jpg"])
    assert calls["resize_to_pixels"][0] == ("a.jpg", 800, 600)


def test_split_n(monkeypatch):
    monkeypatch.setattr(main_mod.dialogs, "ask_value", lambda t, l: "3")
    calls = run(monkeypatch, ["split-n", "a.pdf"])
    assert calls["split_every_n"][0] == ("a.pdf", 3)


def test_compress_custom(monkeypatch):
    monkeypatch.setattr(main_mod.dialogs, "ask_value", lambda t, l: "250")
    calls = run(monkeypatch, ["compress-custom", "a.pdf"])
    assert calls["compress_to_kb"][0] == ("a.pdf", 250)


def test_compress_reports_ladder_steps(monkeypatch):
    calls = run(monkeypatch, ["compress-500", "a.pdf"])
    # the tool fn is a capture stub; progress must still be opened and closed
    assert calls["_progress"].closed


def test_merge_reorder_then_merge(monkeypatch):
    monkeypatch.setattr(main_mod.dialogs, "reorder_dialog", lambda p: ["b.pdf", "a.pdf"])
    calls = run(monkeypatch, ["merge", "a.pdf", "b.pdf"])
    assert calls["merge"][0] == (["b.pdf", "a.pdf"],)


def test_merge_cancel_aborts(monkeypatch):
    monkeypatch.setattr(main_mod.dialogs, "reorder_dialog", lambda p: None)
    calls = run(monkeypatch, ["merge", "a.pdf", "b.pdf"])
    assert "merge" not in calls


import tools_common


def test_acquire_lock_exclusive(tmp_path, monkeypatch):
    monkeypatch.setattr(tools_common, "LOCK_FILE", str(tmp_path / "merge.lock"))
    first = tools_common.acquire_lock()
    assert first is not None
    assert tools_common.acquire_lock() is None        # exclusive
    tools_common.release_lock(first)
    assert tools_common.acquire_lock() is not None    # reusable after release


def test_release_lock_missing_is_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(tools_common, "LOCK_FILE", str(tmp_path / "nope.lock"))
    tools_common.release_lock(str(tmp_path / "nope.lock"))  # no crash


def test_acquire_lock_steals_stale_lock(tmp_path, monkeypatch):
    import time as _t
    lock = tmp_path / "merge.lock"
    monkeypatch.setattr(tools_common, "LOCK_FILE", str(lock))
    lock.write_text("999")
    old = _t.time() - 1000          # a crashed session left this behind
    os.utime(lock, (old, old))
    assert tools_common.acquire_lock() is not None   # stolen, not rejected


def test_wait_queue_stable_returns_after_settle(tmp_path, monkeypatch):
    import time as _t
    q = tmp_path / "q.txt"
    monkeypatch.setattr(tools_common, "QUEUE_FILE", str(q))
    q.write_text("/a.pdf\n/b.pdf\n")
    # grow the file during the first poll window, then let it settle
    orig_stat = os.stat

    def fake_stat(p, *a, **k):
        if str(p) == str(q) and not fake_stat.grown:
            fake_stat.grown = True
            q.write_text("/a.pdf\n/b.pdf\n/c.pdf\n")
        return orig_stat(p, *a, **k)
    fake_stat.grown = False
    monkeypatch.setattr(tools_common.os, "stat", fake_stat)
    items = tools_common.wait_queue_stable(file=str(q), timeout=10, settle=0.2, poll=0.1)
    assert items == ["/a.pdf", "/b.pdf", "/c.pdf"]


def test_wait_queue_stable_empty_queue(tmp_path, monkeypatch):
    assert tools_common.wait_queue_stable(file=str(tmp_path / "missing.txt"),
                                          timeout=2, settle=0.1, poll=0.05) == []


def test_wait_queue_stable_min_len_keeps_waiting(tmp_path):
    import time as _t
    q = tmp_path / "q.txt"
    q.write_text("/a.pdf\n")   # stable from the start, but too few
    t0 = _t.time()
    items = tools_common.wait_queue_stable(file=str(q), timeout=0.5,
                                           settle=0.1, poll=0.05, min_len=2)
    assert items == ["/a.pdf"]
    assert _t.time() - t0 >= 0.4   # waited for late siblings, not early-returned


def test_queue_add_and_read_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(tools_common, "QUEUE_FILE", str(tmp_path / "q.txt"))
    monkeypatch.setattr(tools_common, "LOCK_FILE", str(tmp_path / "lock"))
    tools_common.queue_clear()
    tools_common.queue_add("a.pdf")
    tools_common.queue_add("b.pdf")
    tools_common.queue_add("a.pdf")  # duplicate ignored
    assert tools_common.queue_read() == ["a.pdf", "b.pdf"]
    tools_common.queue_clear()
    assert tools_common.queue_read() == []


def test_queue_add_dispatch(monkeypatch):
    calls = run(monkeypatch, ["queue", "a.pdf"])
    assert calls["_queue"] == ["a.pdf"]


def test_merge_queue_dispatch(monkeypatch):
    monkeypatch.setattr(main_mod.dialogs, "reorder_dialog", lambda p: ["a.pdf", "b.pdf"])
    calls = run(monkeypatch, ["merge-queue", "a.pdf"], queue=["b.pdf", "a.pdf"])
    assert calls["merge"][0] == (["a.pdf", "b.pdf"],)
    assert calls["_queue_cleared"]


def test_merge_queue_too_few(monkeypatch):
    calls = run(monkeypatch, ["merge-queue", "a.pdf"], queue=["a.pdf"])
    assert "merge" not in calls and calls["error"]


def test_merge_queue_cancel_keeps_queue(monkeypatch):
    monkeypatch.setattr(main_mod.dialogs, "reorder_dialog", lambda p: None)
    calls = run(monkeypatch, ["merge-queue", "a.pdf"], queue=["a.pdf", "b.pdf"])
    assert "merge" not in calls and "_queue_cleared" not in calls


def test_merge_selected_winner_merges_queue(monkeypatch):
    events = []
    monkeypatch.setattr(main_mod, "wait_queue_stable", lambda *a, **k: ["b.pdf", "a.pdf"])
    monkeypatch.setattr(main_mod, "acquire_lock", lambda: "lock")
    monkeypatch.setattr(main_mod, "release_lock", lambda p: events.append("release"))
    monkeypatch.setattr(main_mod.dialogs, "reorder_dialog",
                        lambda p: (events.append("dialog"), ["a.pdf", "b.pdf"])[1])
    calls = run(monkeypatch, ["merge-selected", "a.pdf"], queue=["a.pdf", "b.pdf"])
    assert calls["merge"][0] == (["a.pdf", "b.pdf"],)
    assert calls["_queue"] == ["a.pdf"]      # this invocation queued its file
    assert calls["_queue_cleared"]           # queue consumed
    # lock is held through the dialog: released only after it closed
    assert events.index("dialog") < events.index("release")


def test_merge_selected_sibling_exits_silently(monkeypatch):
    monkeypatch.setattr(main_mod, "acquire_lock", lambda: None)  # another invocation owns it
    calls = run(monkeypatch, ["merge-selected", "a.pdf"])
    assert "merge" not in calls
    assert calls["_queue"] == ["a.pdf"]      # still queues its file


def test_merge_selected_too_few_shows_error(monkeypatch):
    monkeypatch.setattr(main_mod, "acquire_lock", lambda: "lock")
    monkeypatch.setattr(main_mod, "wait_queue_stable", lambda *a, **k: ["only.pdf"])
    monkeypatch.setattr(main_mod, "release_lock", lambda p: None)
    calls = run(monkeypatch, ["merge-selected", "only.pdf"])
    assert "merge" not in calls and calls["error"]
    assert calls["_queue_cleared"]           # burst list wiped even on error


def test_merge_selected_cancel_clears_queue(monkeypatch):
    # a canceled dialog must not leak files into the next right-click burst
    monkeypatch.setattr(main_mod, "acquire_lock", lambda: "lock")
    monkeypatch.setattr(main_mod, "wait_queue_stable", lambda *a, **k: ["a.pdf", "b.pdf"])
    monkeypatch.setattr(main_mod, "release_lock", lambda p: None)
    monkeypatch.setattr(main_mod.dialogs, "reorder_dialog", lambda p: None)
    calls = run(monkeypatch, ["merge-selected", "a.pdf"])
    assert "merge" not in calls and calls["_queue_cleared"]


def test_merge_selected_concurrent_single_dialog(tmp_path, monkeypatch):
    import threading
    monkeypatch.setattr(tools_common, "LOCK_FILE", str(tmp_path / "merge.lock"))
    monkeypatch.setattr(main_mod, "MERGE_QUEUE_FILE", str(tmp_path / "ms_queue.txt"))
    dialogs_seen = []
    monkeypatch.setattr(main_mod.dialogs, "reorder_dialog",
                        lambda p: (dialogs_seen.append(sorted(p)), sorted(p))[1])
    monkeypatch.setattr(main_mod, "_progress", lambda *a, **k: None)
    prog = FakeProgress()
    monkeypatch.setattr(main_mod.dialogs, "progress_window", lambda title: prog)
    errors = []
    monkeypatch.setattr(main_mod, "show_error", lambda *a: errors.append(a))
    threads = [threading.Thread(target=main_mod._merge_selected, args=(f"/d/{c}.pdf",))
               for c in "abcde"]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # exactly one dialog, containing all five files
    assert dialogs_seen == [sorted(f"/d/{c}.pdf" for c in "abcde")]
    assert not errors
    assert not os.path.exists(tmp_path / "ms_queue.txt")  # session wiped the list


def test_unknown_action(monkeypatch):
    calls = run(monkeypatch, ["bogus", "a.pdf"])
    assert calls["error"][0].startswith("Unknown action")


def test_pdf_to_images_png(monkeypatch):
    calls = run(monkeypatch, ["pdf-to-images", "a.pdf"])
    assert calls["to_images"][0] == ("a.pdf",)
    assert calls["to_images"][1].get("fmt", "PNG") == "PNG"


def test_pdf_to_images_jpg(monkeypatch):
    calls = run(monkeypatch, ["pdf-to-images-jpg", "a.pdf"])
    assert calls["to_images"][0] == ("a.pdf",)
    assert calls["to_images"][1].get("fmt") == "JPEG"


def test_merge_needs_multiple_files(monkeypatch):
    calls = run(monkeypatch, ["merge", "a.pdf"])
    assert "merge" not in calls and calls["error"]


def test_no_args(monkeypatch):
    calls = run(monkeypatch, [])
    assert calls["error"]
