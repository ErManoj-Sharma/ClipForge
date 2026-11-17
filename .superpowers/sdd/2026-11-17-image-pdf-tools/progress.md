# SDD ledger — plan: /home/manoj/windowsapp/docs/superpowers/plans/2026-11-17-image-pdf-tools.md

Ruling: repo did not exist — initialized git in /home/manoj/windowsapp, single branch, no worktree (no repo to branch from). — cost: no isolated-branch safety; acceptable for a single-author local tool.
Pre-flight: Task1 unique_path → Task2 (consumes) → Task3 (consumes) → Task5 (consumes 1-4) → Task6 (consumes Task5 action names). No conflicts found: signatures match across Interfaces blocks.
Task 1: complete (tests: pytest test_tools_common.py -v → 3/3)
Task 2: complete (tests: pytest test_image_tools.py -v → 7/7; Ruling: pixel resize does not upscale — thumbnail fit-inside; blank test PDF <1KB in Task3 was a test bug, source size raised to 60 pages)
Task 3: complete (tests: pytest test_pdf_tools.py -v → 8/8; Ruling: compress ladder fixed at (150,80)/(110,60)/(72,40), stops at first fit, else writes best-effort smallest)
Task 4: complete (manual GUI smoke on DISPLAY=:0: ask_value enter→"100"/esc→None; ask_pixel_size valid→(1280,720), invalid keeps window open, esc→None; reorder up+merge→reordered, esc→None; Ruling: Listbox move() clears selection before re-setting — Tk selection_set proved additive in this build)
Task 5: complete (tests: pytest test_main.py -v → 11/11; Ruling: logic in main.py, main.pyw is a one-line launcher — .pyw isn't importable by pytest; tools.py namespace re-exports so the router is patchable)
Task 6: complete (sanity: 17 reg verbs → all action strings exist in main.py dispatch, 0 unknown, HKCU-only paths so no admin needed; scripted check in-session, Ruling: HKCU\Software\Classes instead of HKCR — per-user, no elevation)
