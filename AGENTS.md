# AGENTS.md

## What This Project Does

A uv-managed Python package that launches coding agents inside a bubblewrap
sandbox with configurable bind mounts and virtual workspace support.

## Environment & Tooling

- Python >= 3.11, managed with [uv](https://docs.astral.sh/uv/).
- Lint and format:

      uv run ruff check --fix src/bubble_agent && uv run ruff format src/bubble_agent

- Run tests:

      uv run pytest

- Manual verification:

      uv run bubble-agent --dry-run

## Package Layout

Source lives under `src/bubble_agent/` with these modules:

- `cli` — argument parsing and `main()` entry point.
- `config` — config file loading, path expansion, shell variable substitution.
- `workspace` — `.code-workspace` file parsing.
- `sandbox` — bwrap argument construction and command formatting.

## Key Conventions

- Prefer `pathlib.Path` for all path operations instead of `os.path`.
- Workspace folder paths from `.code-workspace` files must go through
  `.expanduser().resolve()` unconditionally.
- Config file values support `~`, `$VAR`/`${VAR}`, and shell built-in vars
  (`UID`, `EUID`, `GID`, `EGID`).
- Config format: `type:source:destination`.
- Use `os.path.exists()` (not `os.path.lexists()`) when checking bind source
  existence — broken symlinks should not pass the check.
- Logging goes to stderr.
  - `--dry-run` / `-D` prints the bwrap command to stderr and exits. Without
  this flag, no command is logged.
- Bwrap args are built as `list[list[str]]` (each inner list = one flag + its
  values), then serialized NUL-separated into an anonymous pipe and passed via
  `--args <fd>` for a clean `ps` listing.
- `subprocess.run` with `pass_fds` is used for reliable fd inheritance
  (preferred over `os.execvp`).
- `/etc/profile` inside the sandbox is patched via `--ro-bind-data` to remove
  the standard ``id -u`` PATH-initialization block and preserve the sandbox
  PATH set by `--setenv`.
- CLI positional args accept directories and `.code-workspace` files (classified
  by suffix).
- `--no-symlink` / `-S` skips symlink creation for workspace folders, preserving
  the original tree structure. Chdir goes to the deepest common ancestor of all
  workspace folder paths (`os.path.commonpath`). Has no effect on plain
  directory args.
