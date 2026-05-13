from __future__ import annotations

import os
from pathlib import Path

from agents import function_tool


def _workspace_root() -> Path:
    return Path(os.getenv("WORKSPACE_PATH", "examples/demo_project")).resolve()


def _safe_path(relative_path: str) -> Path:
    root = _workspace_root()
    target = (root / relative_path).resolve()
    if root != target and root not in target.parents:
        # This prevents prompt-injected paths such as ../../.env from escaping the workspace.
        raise ValueError(f"Path escapes workspace: {relative_path}")
    return target


@function_tool
def list_workspace_files() -> list[str]:
    """List editable files in the configured workflow workspace."""
    root = _workspace_root()
    if not root.exists():
        return []
    ignored = {".git", ".venv", "__pycache__", "node_modules", ".pytest_cache"}
    files: list[str] = []
    for path in root.rglob("*"):
        if any(part in ignored for part in path.parts):
            continue
        if path.is_file():
            files.append(str(path.relative_to(root)))
    return sorted(files)


@function_tool
def read_workspace_file(relative_path: str) -> str:
    """Read a UTF-8 text file from the configured workflow workspace."""
    target = _safe_path(relative_path)
    if not target.exists():
        return f"File does not exist: {relative_path}"
    return target.read_text(encoding="utf-8")


@function_tool
def write_workspace_file(relative_path: str, content: str) -> str:
    """Write a UTF-8 text file inside the configured workflow workspace."""
    target = _safe_path(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {relative_path}"
