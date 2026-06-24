# bubble-agent

> This project is inspired by [cyunrei/opencode-bwrap](https://github.com/cyunrei/opencode-bwrap).

Run your coding agent in a bubble.

Uses [bubblewrap](https://github.com/containers/bubblewrap) to sandbox coding agents with configurable bind
mounts and virtual workspace (.code-workspace) support.

By default, the sandbox wraps [opencode](https://github.com/anomalyco/opencode). Use `--bin` to run a different coding agent.

## Quick Start

### Install

```shell
git clone https://github.com/ak1ra-lab/bubble-agent.git
cd bubble-agent
make install
```

Make sure `~/.local/bin` is in your `PATH`.

### Run

```shell
bubble-agent                              # runs opencode by default

# Pass arguments to the coding agent after --
bubble-agent -- serve                     # opencode subcommand
bubble-agent -- --prompt "write a test"   # opencode flags

# Work in a specific directory
bubble-agent ~/my-project

# Work in multiple directories
bubble-agent ~/frontend ~/backend

# Use a .code-workspace file (flattened view with symlinks)
bubble-agent ~/projects/my.code-workspace

# Use a .code-workspace file (preserve original tree, e.g. Ansible projects)
bubble-agent -S ~/ansible.code-workspace

# Mix directories and .code-workspace files
bubble-agent ~/lib ~/my.code-workspace

# Use a different agent
bubble-agent --bin claude

# Use a custom config file
bubble-agent -c /path/to/custom.conf

# Dry-run: print the bwrap command without executing
bubble-agent --dry-run
```

## Configuration

Config file: `~/.config/bubble-agent/bubble-agent.conf`

Override via CLI flags:

| Flag                 | Default                                                                   |
| -------------------- | ------------------------------------------------------------------------- |
| `[paths...]`         | auto-bind `$PWD` if none given                                            |
| `-c`, `--config`     | `$BUBBLE_AGENT_CONFIG_FILE` or `~/.config/bubble-agent/bubble-agent.conf` |
| `--bin`              | `$BUBBLE_AGENT_BIN` or `opencode`                                         |
| `-S`, `--no-symlink` | preserve original tree structure in workspace                             |
| `--dry-run`          | print command only, do not execute                                        |

Environment variables `BUBBLE_AGENT_CONFIG_FILE` and `BUBBLE_AGENT_BIN` are still honored as fallback defaults.

Format: `type:source:destination`. Both source and destination support `~` for `$HOME` and environment variables (`$VAR`, `${VAR}`).

For security, **only configured paths are accessible** inside the sandbox. Copy `bubble-agent.example.conf` to `~/.config/bubble-agent/bubble-agent.conf` and customize - it documents all available bind types and includes recommended toolchain, git, and agent entries.

### Virtual Workspace (`.code-workspace`)

Pass a VS Code-style `.code-workspace` JSON file as a positional argument.

By default, folder paths are symlinked into `~/workspace/` inside the sandbox (flattened view):

```shell
bubble-agent ~/projects/my.code-workspace
```

```jsonc
// ~/projects/my.code-workspace
{
  "folders": [
    { "path": "/home/user/frontend-app", "name": "frontend" },
    { "path": "/home/user/backend-api", "name": "backend" },
    { "path": "../libs/shared-utils", "name": "shared" },
  ],
}
```

Inside the sandbox:

```
~/workspace/
  frontend/  -> /home/user/frontend-app
  backend/   -> /home/user/backend-api
  shared/    -> /home/user/libs/shared-utils
```

#### Preserving Original Tree (`-S` / `--no-symlink`)

For projects like Ansible collections that depend on a specific directory layout, pass `-S` to skip symlink creation and chdir to the deepest common ancestor of all workspace folders instead:

```shell
bubble-agent -S ~/ansible.code-workspace
```

This bind-mounts only the real paths, so the original `ansible/collections/ansible_collections/...` hierarchy is visible as-is. Relative paths are resolved relative to the `.code-workspace` file's location. Duplicate folder names get a `_N` suffix appended.

## Uninstall

```shell
make uninstall
```

Optionally remove the config directory:

```shell
rm -rf ~/.config/bubble-agent
```

## Dependencies

- Python >= 3.11
- `bwrap` (bubblewrap)
- A coding agent binary (default: `opencode`, in PATH)
