# Configuration

Config file: `~/.config/bubble-agent/bubble-agent.conf`

Override via CLI flags: `-c` / `--config`.

## Format

```
type:source:destination
```

Both source and destination support `~` for `$HOME` and environment variables (`$VAR`, `${VAR}`). The special shell built-in variables `UID`, `EUID`, `GID`, `EGID` are also expanded.

## Bind Types

| Type            | Description                                                  |
| --------------- | ------------------------------------------------------------ |
| `bind`          | Read-write bind mount (source must exist)                    |
| `ro-bind`       | Read-only bind mount (source must exist)                     |
| `bind-try`      | Read-write bind mount (ignored if source doesn't exist)      |
| `ro-bind-try`   | Read-only bind mount (ignored if source doesn't exist)       |
| `symlink`       | Create a symbolic link                                       |
| `env` / `setenv`| Set an environment variable (`env:VAR_NAME:VAR_VALUE`)       |
| `path-prepend`  | Prepend a directory to the sandbox `PATH`                    |
| `path-append`   | Append a directory to the sandbox `PATH`                     |

## PATH Handling

By default, the sandbox inherits the host `PATH`. The `path-prepend` and `path-append` config entries add directories before or after the inherited `PATH`. Prepended directories take priority over inherited entries, and duplicates are removed (first occurrence wins).

If you set an explicit `env:PATH:...` in the config, the inherited path is **skipped** — only the explicit value is used.

## Shell Configuration

Shell rc files (`~/.bashrc`, `~/.bash_profile`, etc.) are **not** bound by default. Coding agents invoke tools directly and do not source shell init files.

If your agent runs shell commands that need custom aliases, functions, or environment setup, add the relevant files to your config:

```
ro-bind:~/.bashrc:~/.bashrc
```

!!! note
    Since `--clearenv` is applied, even bound rc files won't be sourced automatically — the agent would need to explicitly source them. Most coding agents don't need this.

For security, **only configured paths are accessible** inside the sandbox. Copy `bubble-agent.example.conf` to `~/.config/bubble-agent/bubble-agent.conf` and customize — it documents all available bind types and includes recommended toolchain, git, and agent entries.
