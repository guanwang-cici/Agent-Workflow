from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel


class CommandResult(BaseModel):
    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


def _allowed_commands() -> set[str]:
    raw = os.getenv("WORKFLOW_ALLOWED_COMMANDS", "pytest,npm test,npm run test,python -m pytest")
    return {item.strip() for item in raw.split(",") if item.strip()}


def run_allowed_command(command: str, cwd: Path, timeout_seconds: int = 120) -> CommandResult:
    allowed = _allowed_commands()
    normalized = " ".join(shlex.split(command))
    if normalized not in allowed:
        # This is the main safety boundary for local command execution.
        raise ValueError(f"Command is not allowed: {command}. Allowed commands: {sorted(allowed)}")

    args = shlex.split(normalized)
    if args and args[0] == "python":
        # Keep configuration portable on machines where only python3 is on PATH.
        args[0] = sys.executable

    completed = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    return CommandResult(
        command=normalized,
        returncode=completed.returncode,
        stdout=completed.stdout[-4000:],
        stderr=completed.stderr[-4000:],
    )
