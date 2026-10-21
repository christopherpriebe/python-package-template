# Python package template

A Copier template for typed Python packages with optional Rust bindings. The
root of this repo is the template's own tooling; everything under `template/`
is Jinja source that Copier renders into a new project.

## Layout

- `copier.yml`: questions, defaults, validators. `python_max` is the newest
  CPython a generated project tests against.
- `template/`: the rendered project. Files ending in `.jinja` are rendered;
  everything else is copied verbatim. A file name wrapped in
  `{% if cond %}...{% endif %}` is omitted when the condition is false.
- `template/CLAUDE.md.jinja` and `template/.claude/`: the agent setup every
  generated project ships with. A change here reaches every project on its
  next `copier update`, so keep it general and keep it short.
- `noxfile.py`: the self-test. Renders both variants and runs their full nox
  suites.
- `README.md`: user-facing docs. Its "Layout of a generated project" and
  "Choices baked in" sections describe `template/`; update them in the same
  change as the template.

## Testing changes

    uvx nox                        # both variants, every default session
    uvx nox -s generated-pure      # one variant
    uvx nox -- -s lint typecheck   # pass a session selection through

The self-test renders from `HEAD`, so the repo needs at least one commit;
uncommitted changes are included. To inspect a render by hand:

    uvx copier copy --defaults --vcs-ref=HEAD --data use_rust=true . /tmp/render

## Conventions

- Render-time logic is limited to `use_rust`, `license`, and `github_owner`.
  Taste preferences are not Copier questions; they are edited in the
  generated files.
- GitHub Actions `${{ }}` expressions need `{% raw %}` blocks.
- Tool version floors live in `template/pyproject.toml.jinja` and
  `template/.pre-commit-config.yaml.jinja`, action versions in the release
  workflow. Bump deliberately and run the self-test.
- When a new CPython ships, bump `python_max` in `copier.yml` and the
  `python_min` choices list.
- Never patch a rendered project to fix a template bug; fix the template and
  re-render.
- Hook scripts under `template/.claude/hooks/` are copied verbatim and are
  linted and type-checked by the generated project's own gate.

## Why the agent setup is small

It follows the 2026 evidence rather than the maximal version:

- Context files do not improve task success and cost over 20% more
  inference (Gloaguen et al., arXiv 2602.11988; Khatri, arXiv 2607.27250).
  Agents do follow instructions in them, so `CLAUDE.md` holds commands and
  non-default conventions only, and never a repository overview.
- Instruction adherence decays within a session (McMillan, arXiv
  2605.10039). Hooks and a read-only reviewer enforce what prose cannot.
- A reporting channel for defective tests plus a no-hacking policy cut
  reward hacking from 23.6% to 5.3% across eight models (arXiv 2608.29460).
  Both are in `CLAUDE.md` and the agent briefs.
- Multi-agent pipelines rarely beat one strong agent (MAST, arXiv
  2503.13657). Subagents exist for isolation and verification, and for a
  cheaper implementation tier by the maintainer's choice.

Grow the rules from failures that recur, not from speculation.
