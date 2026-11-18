import os
import tools_common


def test_returns_input_when_absent(tmp_path):
    p = str(tmp_path / "a.txt")
    assert tools_common.unique_path(p) == p


def test_returns_1_suffix_when_taken(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("x")
    assert tools_common.unique_path(str(p)) == str(tmp_path / "a_1.txt")


def test_skips_to_free_suffix(tmp_path):
    a = tmp_path / "a.txt"
    a.write_text("x")
    (tmp_path / "a_1.txt").write_text("x")
    assert tools_common.unique_path(str(a)) == str(tmp_path / "a_2.txt")
