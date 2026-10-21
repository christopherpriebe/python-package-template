# Python package template

A [Copier](https://copier.readthedocs.io/) template for typed Python packages,
with optional Rust bindings.

- **uv** for environments, locking, building, and publishing
- **ruff** with a curated, strict rule set, including pydoclint (`DOC`)
- **ty** with every rule set to error
- **pytest** with pytest-xdist and pytest-cov
- **nox** for full local runs: lint, type check, tests on every supported
  Python, combined coverage, Rust checks, docs
- **Sphinx** docs with the Read the Docs theme, Google-style docstrings
- **pre-commit** hooks that run ruff and ty from `uv.lock`
- **Rust (optional)**: Cargo workspace with a pure-Rust core crate and a PyO3
  bindings crate, built by maturin as an abi3 wheel
- **Release workflow**: the only GitHub Actions workflow; builds and publishes to
  PyPI on a `v*` tag
- **Claude Code setup**: a short committed `CLAUDE.md`, path-scoped rules,
  model-tiered subagents, skills for plan/feature/fix-gate/release/marathon,
  a format-on-edit hook, a stop-gate hook, a usage-aware status line and
  guard for multi-hour runs, and a permission allowlist

## Create a project

```console
uvx copier copy --trust gh:<you>/<this-repo> my-project
```

`--trust` is not required today (the template runs no tasks), but is harmless.
Copier asks for the project name, author, license, minimum Python, and whether
to include Rust. Then:

```console
cd my-project
git init && git add -A
uv sync
uv run pre-commit install
uv run nox
```

To skip retyping your name and email every time, put defaults in Copier's
settings file (`~/.config/copier/settings.yml` on Linux,
`~/Library/Application Support/copier/settings.yml` on macOS):

```yaml
defaults:
  author_name: Your Name
  author_email: you@example.com
  github_owner: your-github-user
```

## Update an existing project

Projects record the template version in `.copier-answers.yml`. After changing
the template, tag it (`git tag v1.1.0 && git push --tags`), then in a project:

```console
uvx copier update
```

Copier merges template changes with your edits and leaves conflicts marked.

## Layout of a generated project

```text
.
├── pyproject.toml          # metadata, dependency groups, ruff, ty, pytest, coverage
├── noxfile.py              # lint, typecheck, tests, coverage, rust, docs, build, bump
├── .pre-commit-config.yaml
├── .github/workflows/release.yml   # omitted for Proprietary
├── CLAUDE.md               # agent entry point: commands, definition of done, model tiers
├── .claude/
│   ├── settings.json       # permissions and hooks
│   ├── rules/              # python, tests, dependencies, rust (Rust variant)
│   ├── agents/             # scout, implementer, reviewer
│   ├── skills/             # plan, feature, fix-gate, release, marathon
│   ├── hooks/              # format_file, stop_gate, statusline, usage_guard, marathon_driver
│   └── workflows/          # feature.js
├── src/<package>/
│   ├── __init__.py
│   ├── _core.py            # pure Python variant
│   ├── _core.pyi           # Rust variant: stubs for the extension
│   └── py.typed
├── tests/
├── docs/                   # Sphinx: conf.py, index, api, development
├── Cargo.toml              # Rust variant: workspace, lints, pyo3
└── crates/
    ├── <crate>/            # pure Rust library
    └── <crate>-py/         # PyO3 bindings -> <package>._core
```

## Choices baked in

**Ruff rules.** Selected: `A ANN ARG ASYNC B BLE C4 D DTZ E EM ERA F FBT FLY
FURB G I ICN INP ISC LOG N PERF PGH PIE PL PT PTH PYI RET RSE RUF S SIM SLF
SLOT T10 T20 TID TRY UP W YTT`, plus pydoclint `DOC201 DOC202 DOC402 DOC403
DOC501 DOC502` (preview, opted in one rule at a time). Ignored: `D105` and
`D107` (no docstrings on dunder methods), `E501` (formatter's job), `FBT003`,
and `ISC001` (formatter conflict). Tests may use `assert`, magic numbers, and
skip docstrings. Not selected: `C90`, `TC`, `COM`, `Q`, `CPY`, `TD`, `FIX`,
`EXE`, `FA`, and framework rules (`AIR`, `DJ`, `FAST`, `NPY`, `PD`, `INT`).

**ty.** `all = "error"`, warnings fail the run, and `# type: ignore` is not
honored, so suppressions must be `# ty: ignore[rule]`. The `typecheck` nox
session runs ty once per supported Python version.

**pytest.** Native `[tool.pytest]` config with `strict = true`,
`--import-mode=importlib`, `-n auto --dist worksteal`, and warnings as errors.
Use `-n0` to run serially when debugging.

**Coverage.** Branch coverage, combined across Python versions, failing under
90%.

**Versioning.** Static version in `pyproject.toml`. `nox -s bump -- minor` runs
`uv version --bump` and, with Rust, updates the Cargo workspace version and
`Cargo.lock` to match. The release workflow refuses a tag that doesn't match.

**Rust.** Edition 2024, `clippy::pedantic` plus `unwrap_used`/`expect_used`/
`panic`/`todo` as warnings, `unsafe_code` denied, `missing_docs` warned;
clippy runs with `--deny=warnings`. PyO3 uses the `abi3-py3XX` feature for the
minimum Python, so each platform gets one wheel. `uv sync`/`uv run` rebuild
the extension when anything under `crates/` changes.

**Agents.** `CLAUDE.md` stays short and holds commands, the definition of done,
and a model-tier table (opus plans and reviews, sonnet implements, haiku reads;
never fable unless asked). Style rules live in `.claude/rules/` and load only
when a matching path is touched. Subagents pin a model and a tool set: the
reviewer cannot edit, the scout can only read, the implementer never touches
`tests/`. A defective test is reported, never edited. Hooks format every edited
file and refuse to end a turn while ruff, ty, or the tests fail. For
multi-hour work, `/marathon` keeps a run ledger and commits a checkpoint per
step; the status line records the subscription usage windows, a guard warns
at 80% and allows only checkpoint actions at 92%, and a stop hook keeps an
active run moving. Personal overrides go in
`CLAUDE.local.md` and `.claude/settings.local.json`, both gitignored.

## Maintaining the template

- Bump `python_max` in `copier.yml` when a new CPython is released.
- Bump tool floors in `template/pyproject.toml.jinja` and action versions in
  the release workflow as needed.
- Run `uvx nox` here to render both variants and run their full checks.
- The agent setup under `template/.claude/` reaches every project on
  `copier update`; keep it general, and grow rules from recurring failures
  rather than speculation.
