import sys
import main as main_mod


class FakeProgress:
    def __init__(self):
        self.texts = []
        self.closed = False

    def __call__(self, text):
        self.texts.append(text)

    def close(self):
        self.closed = True


def run(monkeypatch, argv, **overrides):
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


def test_unknown_action(monkeypatch):
    calls = run(monkeypatch, ["bogus", "a.pdf"])
    assert calls["error"][0].startswith("Unknown action")


def test_merge_needs_multiple_files(monkeypatch):
    calls = run(monkeypatch, ["merge", "a.pdf"])
    assert "merge" not in calls and calls["error"]


def test_no_args(monkeypatch):
    calls = run(monkeypatch, [])
    assert calls["error"]
