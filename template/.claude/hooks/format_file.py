"""Format a file after Claude edits it.

Claude Code runs this as a ``PostToolUse`` hook for ``Edit`` and ``Write``.
It reads the hook payload from stdin, finds the edited file, and runs the
project's formatter on it: ruff from the project environment for Python,
``cargo fmt`` for Rust when the project has a ``Cargo.toml``. Other files are
ignored. A formatter failure, usually a syntax error, exits with status 2 so
the error reaches Claude.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

PYTHON_SUFFIXES = frozenset({".py", ".pyi"})
FORMATTER_FAILED = 2


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


def _edited_file(payload: dict[str, object]) -> Path | None:
    """Return the file the tool call touched.

    Args:
        payload: The hook payload.

    Returns:
        The path from ``tool_input.file_path``, or ``None`` if absent.
    """
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    file_path = tool_input.get("file_path")
    return Path(file_path) if isinstance(file_path, str) and file_path else None


def main() -> int:
    """Format the edited file with the matching formatter.

    Returns:
        ``0`` when nothing needed formatting or formatting succeeded, and
        ``2`` when the formatter reported an error.
    """
    payload = _payload()
    file = _edited_file(payload)
    if file is None or not file.is_file():
        return 0
    project_dir = Path(str(payload.get("cwd", ".")))
    if file.suffix in PYTHON_SUFFIXES:
        ruff = shutil.which("ruff") or str(Path(sys.executable).with_name("ruff"))
        result = subprocess.run([ruff, "format", "--quiet", str(file)], check=False)
    elif file.suffix == ".rs" and (project_dir / "Cargo.toml").is_file():
        result = subprocess.run(
            ["cargo", "fmt", "--all", "--quiet"], cwd=project_dir, check=False
        )
    else:
        return 0
    return FORMATTER_FAILED if result.returncode != 0 else 0


if __name__ == "__main__":
    sys.exit(main())
