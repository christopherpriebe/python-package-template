"""Self-test for the template: render each variant and run its nox sessions.

    uvx nox                       # every variant, every default session
    uvx nox -s generated-rust     # one variant
    uvx nox -- -s lint typecheck  # pass a session selection to the generated nox

Uncommitted template changes are included (copier --vcs-ref=HEAD).
"""

import shutil
from pathlib import Path

import nox

nox.options.default_venv_backend = "none"

ROOT = Path(__file__).parent

ANSWERS = {
    "project_name": "Template Check",
    "description": "Rendered by the template self-test.",
    "author_name": "Template Check",
    "author_email": "check@example.com",
    "github_owner": "example",
}


VARIANTS = {
    "pure": {"use_rust": "false"},
    "rust": {"use_rust": "true"},
    "proprietary": {"use_rust": "true", "license": "Proprietary"},
}


@nox.session
@nox.parametrize("variant", list(VARIANTS))
def generated(session: nox.Session, variant: str) -> None:
    """Render the template and run the generated project's nox sessions."""
    dest = Path(session.create_tmp()) / variant
    shutil.rmtree(dest, ignore_errors=True)

    data = {**ANSWERS, **VARIANTS[variant]}
    session.run(
        "uvx",
        "copier",
        "copy",
        "--defaults",
        "--vcs-ref=HEAD",
        *(arg for key, value in data.items() for arg in ("--data", f"{key}={value}")),
        str(ROOT),
        str(dest),
        external=True,
    )

    session.chdir(dest)
    session.run("git", "init", "--quiet", external=True)
    session.run("uv", "sync", external=True)
    session.run("uv", "run", "nox", *session.posargs, external=True)
