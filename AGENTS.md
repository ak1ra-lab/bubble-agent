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
- Config file values support `~`, `$VAR`/`${VAR}`, and shell built-in vars
  (`UID`, `EUID`, `GID`, `EGID`).
- Config format: `type:source:destination`.
- Use `os.path.exists()` (not `os.path.lexists()`) when checking bind source
  existence — broken symlinks should not pass the check.
- Logging goes to stderr.
  - `--dry-run` / `-D` prints the bwrap command to stderr and exits. Without
  this flag, no command is logged.
- Bwrap args are built as `list[list[str]]` (each inner list = one flag + its
  values), flattened at exec time.
- CLI positional args accept directories and `.code-workspace` files (classified
  by suffix).
- `--no-symlink` / `-S` skips symlink creation for workspace folders, preserving
  the original tree structure. Chdir goes to the deepest common ancestor of all
  workspace folder paths (`os.path.commonpath`). Has no effect on plain
  directory args.

## Sandbox Layout

- `/usr` and `/etc` are read-only bind mounts; `/lib*` and `/sys` use
  `ro-bind-try`.
- `/bin` and `/sbin` are symlinks to `usr/bin` and `usr/sbin`.
- `/proc`, `/tmp`, `/run` are tmpfs; `/dev` is a minimal devfs.
- `/var` is an empty directory; `/var/tmp` is a symlink to `/tmp`.
- `XDG_RUNTIME_DIR` is set to `/run/user/$UID`.
- `--dir $HOME` is created in all code paths (auto-bound cwd, explicit
  directory args, workspace files).

## PATH Handling

- By default, the sandbox **inherits the host `PATH`**. This is intentional:
  `/usr` is already ro-bind-mounted, so most system tools are accessible.
- `path-prepend` and `path-append` config entries add directories before/after
  the inherited PATH.
- If an explicit `env:PATH:...` is set in config, the inherited PATH is
  **skipped entirely** — only the explicit value is used.
- Prepended directories take priority over inherited entries; duplicates are
  removed (first occurrence wins).

## Shell Config Files

- Shell rc files (`~/.bashrc`, `~/.bash_profile`, etc.) are **not** bound by
  default. Coding agents typically invoke tools directly and do not source
  shell init files.
- If an agent runs shell commands that need custom aliases, functions, or
  environment setup, bind the relevant rc files:
  ```
  ro-bind:~/.bashrc:~/.bashrc
  ```
- Since `--clearenv` is applied, even bound rc files won't be sourced
  automatically — the agent would need to explicitly source them.
