import base64
import io
import zipfile

import build_installer


def test_payload_contains_all_files():
    z = zipfile.ZipFile(io.BytesIO(build_installer.build_zip()))
    assert set(z.namelist()) == set(build_installer.FILES)


def test_generated_cmd_roundtrips(tmp_path):
    out = build_installer.build(str(tmp_path / "s.cmd"))
    text = open(out, encoding="ascii").read()
    payload = text[text.rindex(build_installer.MARKER) + len(build_installer.MARKER):]
    z = zipfile.ZipFile(io.BytesIO(base64.b64decode(payload)))
    assert set(z.namelist()) == set(build_installer.FILES)


def test_generated_cmd_runs_setup():
    text = build_installer.render()
    assert "Expand-Archive" in text
    assert "setup.ps1" in text
    # payload is after the marker and contains base64, not the zipped files
    payload = text[text.rindex(build_installer.MARKER) + len(build_installer.MARKER):]
    assert "MagicPK" not in payload  # zip magic not in plaintext
