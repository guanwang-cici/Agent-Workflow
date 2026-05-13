from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.tools.command_runner import run_allowed_command


def test_run_allowed_command_rejects_unknown_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WORKFLOW_ALLOWED_COMMANDS", "python -m pytest")

    with pytest.raises(ValueError):
        run_allowed_command("rm -rf .", tmp_path)


def test_run_allowed_command_accepts_allowlisted_command(monkeypatch: pytest.MonkeyPatch) -> None:
    workspace = Path("examples/demo_project").resolve()
    monkeypatch.setenv("WORKFLOW_ALLOWED_COMMANDS", "python -m pytest")

    result = run_allowed_command("python -m pytest", workspace)

    assert result.passed
    assert result.command == "python -m pytest"
