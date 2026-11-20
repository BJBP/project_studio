# custom_integration.py: picks only custom_components/<id> from a release archive, with no path escapes.
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "stack" / "domotica-voz" / "setup"))
import custom_integration  # noqa: E402


def archive(files: dict) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def test_takes_only_the_component_folder():
    raw = archive({"repo-1/custom_components/sonoff/__init__.py": b"x", "repo-1/custom_components/sonoff/core/a.py": b"y",
                   "repo-1/README.md": b"z", "repo-1/custom_components/other/b.py": b"w"})
    assert sorted(custom_integration.component_files(raw, "sonoff")) == [("__init__.py", b"x"), ("core/a.py", b"y")]


def test_rejects_path_escapes_and_missing_component():
    raw = archive({"repo-1/custom_components/sonoff/../../evil.py": b"x"})
    with pytest.raises(custom_integration.InstallError, match="E_ARCHIVE"):
        custom_integration.component_files(raw, "sonoff")


def test_every_catalog_entry_is_pinned():
    for item in json.loads(custom_integration.CATALOG.read_text(encoding="utf-8"))["integrations"]:
        assert item["tag"].startswith("v") and item["license"] and "/" in item["repo"]
