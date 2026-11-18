import tkinter as tk


def _center(win, w, h):
    win.update_idletasks()
    x = (win.winfo_screenwidth() - w) // 2
    y = (win.winfo_screenheight() - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


def _base_window(title, w, h):
    win = tk.Tk()
    win.title(title)
    win.overrideredirect(True)  # borderless
    _center(win, w, h)
    win.attributes("-topmost", True)
    win.focus_force()  # launched from Explorer: otherwise it can open behind other windows
    return win


def _run_ok_esc(win, on_ok):
    win.bind("<Escape>", lambda e: win.destroy())
    win.bind("<Return>", lambda e: on_ok())


def ask_value(title, label):
    """One input; Enter -> value string, Esc/close -> None."""
    result = []

    def ok():
        result.append(entry.get().strip())
        win.destroy()

    win = _base_window(title, 320, 90)
    tk.Label(win, text=label, anchor="w").pack(fill="x", padx=12, pady=(12, 4))
    entry = tk.Entry(win)
    entry.pack(fill="x", padx=12)
    entry.focus_set()
    tk.Button(win, name="ok", text="OK", width=10, command=ok).pack(pady=8)
    _run_ok_esc(win, ok)
    win.mainloop()
    return result[0] if result and result[0] else None


def ask_pixel_size():
    """'W x H' input; Enter -> (w, h) tuple, Esc/close or invalid -> None."""
    result = []

    def ok():
        raw = entry.get().strip().lower().replace("*", "x")
        parts = raw.split("x")
        try:
            w, h = int(parts[0]), int(parts[1])
            result.append((w, h))
            win.destroy()
        except (ValueError, IndexError):
            entry.delete(0, "end")
            entry.insert(0, "use e.g. 1280 x 720")

    win = _base_window("Resize to Pixel Size", 320, 90)
    tk.Label(win, text="Pixel size (e.g. 1280 x 720):", anchor="w").pack(fill="x", padx=12, pady=(12, 4))
    entry = tk.Entry(win)
    entry.pack(fill="x", padx=12)
    entry.focus_set()
    tk.Button(win, name="ok", text="OK", width=10, command=ok).pack(pady=8)
    _run_ok_esc(win, ok)
    win.mainloop()
    return result[0] if result else None


def progress_window(title):
    """Small 'Working...' window. Returns update(text) with .close().
    Each update repainting the window is what keeps it alive during
    synchronous work (pyw has no console, nothing else pumps events)."""
    win = _base_window(title, 360, 70)
    lbl = tk.Label(win, text="Working...", anchor="w")
    lbl.pack(fill="x", padx=12, pady=16)

    def update(text):
        lbl.config(text=text)
        win.update()

    update.close = win.destroy
    return update


def reorder_dialog(paths):
    """List of files with Up/Down; 'Merge' -> reordered list, Cancel/close -> None."""
    result = []

    def move(delta):
        sel = box.curselection()
        if not sel:
            return
        i = sel[0]
        j = i + delta
        if 0 <= j < box.size():
            item = box.get(i)
            box.delete(i)
            box.insert(j, item)
            box.selection_clear(0, "end")
            box.selection_set(j)
            box.activate(j)

    win = _base_window("Merge PDFs - set order (top = first)", 420, 320)
    box = tk.Listbox(win, selectmode="browse", name="list")
    for p in paths:
        box.insert("end", p)
    box.pack(fill="both", expand=True, padx=10, pady=10)
    box.selection_clear(0, "end")
    box.selection_set(0)
    btns = tk.Frame(win)
    tk.Button(btns, name="up", text="Up", width=8, command=lambda: move(-1)).pack(side="left", padx=4)
    tk.Button(btns, name="down", text="Down", width=8, command=lambda: move(1)).pack(side="left", padx=4)
    btns.pack()

    def ok():
        result.extend(box.get(0, "end"))
        win.destroy()

    tk.Button(win, name="merge", text="Merge", width=12, command=ok).pack(pady=(0, 10))
    _run_ok_esc(win, ok)
    win.mainloop()
    return list(result) if result else None
