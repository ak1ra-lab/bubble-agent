# AGENTS.md

## What This Project Does

A single-file Python script that launches coding agents inside a bubblewrap
sandbox with configurable bind mounts and virtual workspace support.

## Environment & Tooling

- Python >= 3.11 (only stdlib, no package manager or `requirements.txt`)
- Lint and format:

      ruff check --fix bubble-agent && ruff format bubble-agent

- No automated tests. Manually verify with:

      python3 bubble-agent --dry-run

## Key Conventions

- Prefer `pathlib.Path` for all path operations instead of `os.path`.
- Workspace folder paths from `.code-workspace` files must go through
  `.expanduser().resolve()` unconditionally.
- Config file values support `~` and `$VAR`/`${VAR}` expansion.
- Config format: `type:source:destination`.
- Logging goes to stderr.
  - `--dry-run` logs the bwrap command and skips execution.
- Bwrap args are built as `list[list[str]]` (each inner list = one flag + its
  values), flattened at exec time.
- CLI positional args accept directories and `.code-workspace` files (classified
  by suffix).
- `--no-symlink` / `-S` skips symlink creation for workspace folders, preserving
  the original tree structure. Chdir goes to the first workspace file's parent
  directory. Has no effect on plain directory args.
