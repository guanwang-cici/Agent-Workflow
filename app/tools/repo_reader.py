from __future__ import annotations

from pathlib import Path


IGNORED_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".pytest_cache"}


def build_repo_snapshot(workspace_path: Path, max_files: int = 80, max_chars: int = 12_000) -> str:
    """Return a bounded repo snapshot so agent prompts stay small and deterministic."""
    workspace = workspace_path.resolve()
    if not workspace.exists():
        return f"Workspace does not exist: {workspace}"

    lines: list[str] = [f"Workspace: {workspace}", "Files:"]
    files: list[Path] = []
    for path in workspace.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
        if len(files) >= max_files:
            break

    for path in files:
        lines.append(f"- {path.relative_to(workspace)}")

    sample_budget = max_chars - sum(len(line) + 1 for line in lines)
    if sample_budget <= 0:
        return "\n".join(lines)

    lines.append("\nSmall text file excerpts:")
    for path in files:
        if path.suffix not in {".py", ".js", ".ts", ".tsx", ".json", ".md", ".txt", ".toml", ".yaml", ".yml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        excerpt = text[: min(1200, sample_budget)]
        if not excerpt:
            continue
        lines.append(f"\n--- {path.relative_to(workspace)} ---\n{excerpt}")
        sample_budget -= len(excerpt)
        if sample_budget <= 0:
            break

    return "\n".join(lines)
