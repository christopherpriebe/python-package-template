"""Refuse to end a turn while the fast checks fail.

Claude Code runs this as a ``Stop`` hook. When the working tree has
uncommitted changes, it runs ruff, ty, and pytest from the project
environment. If any fails, it exits with status 2 and prints the output to stderr, which
hands the failures back to Claude instead of ending the turn. A clean tree,
or a turn that is already continuing because of this hook, passes through.
"""

import json
import subprocess
import sys
from pathlib import Path

GATE_FAILED = 2
CHECKS: tuple[tuple[str, ...], ...] = (
    ("ruff", "format", "--check", "."),
    ("ruff", "check", "."),
    ("ty", "check"),
    ("pytest", "--quiet", "--exitfirst", "--no-header"),
)


def _payload() -> dict[str, object]:
    """Read the hook payload from stdin.

    Returns:
        The decoded JSON object, or an empty dict if stdin is not a JSON
        object.
    """
    try:
        payload: object = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {str(key): value for key, value in payload.items()}


def _tree_is_clean(project_dir: Path) -> bool:
    """Report whether git sees no changes in the project.

    Args:
        project_dir: The directory to inspect.

    Returns:
        ``True`` when ``git status`` succeeds and prints nothing.
    """
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    return status.returncode == 0 and not status.stdout.strip()


def _run_check(argv: tuple[str, ...], project_dir: Path) -> str | None:
    """Run one check from the project environment.

    Args:
        argv: The command; its first element is resolved next to the running
            interpreter.
        project_dir: The directory to run in.

    Returns:
        The command and its output when it failed, or ``None`` when it passed.
    """
    tool = Path(sys.executable).with_name(argv[0])
    result = subprocess.run(
        [str(tool), *argv[1:]],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return None
    return f"$ {' '.join(argv)}\n{result.stdout}{result.stderr}".rstrip()


def main() -> int:
    """Run the fast checks and block the stop if any fail.

    Returns:
        ``0`` to let the turn end, ``2`` to hand failures back to Claude.
    """
    payload = _payload()
    if payload.get("stop_hook_active"):
        return 0
    project_dir = Path(str(payload.get("cwd", ".")))
    if _tree_is_clean(project_dir):
        return 0
    failures = [_run_check(argv, project_dir) for argv in CHECKS]
    reports = [failure for failure in failures if failure is not None]
    if not reports:
        return 0
    sys.stderr.write("Stop gate failed. Fix these before finishing:\n\n")
    sys.stderr.write("\n\n".join(reports) + "\n")
    return GATE_FAILED


if __name__ == "__main__":
    sys.exit(main())
