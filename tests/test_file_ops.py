from __future__ import annotations

from pathlib import Path

import pytest

from app.tools import file_ops


def test_write_workspace_file_rejects_path_escape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WORKSPACE_PATH", str(tmp_path))

    with pytest.raises(ValueError):
        file_ops._safe_path("../escape.txt")
