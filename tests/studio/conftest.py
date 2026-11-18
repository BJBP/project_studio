import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio.presentation.wiring import build_repo  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    return build_repo(tmp_path / "datos")
