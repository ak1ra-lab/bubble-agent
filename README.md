# bubble-agent

> This project is inspired by [cyunrei/opencode-bwrap](https://github.com/cyunrei/opencode-bwrap).

Sandboxed runtime for coding agents using [bubblewrap](https://github.com/containers/bubblewrap) with configurable bind mounts and virtual workspace support.

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

# Use a different agent
bubble-agent --bin claude

# Use a custom config file
bubble-agent -c /path/to/custom.conf

# Enable a .code-workspace for multi-repo workflows
bubble-agent --workspace ~/projects/my.code-workspace

# Dry-run: print the bwrap command without executing
bubble-agent --dry-run
```

## Configuration

Config file: `~/.config/bubble-agent/bubble-agent.conf`

Override via CLI flags:

| Flag                | Default                                        |
| ------------------- | ---------------------------------------------- |
| `-c`, `--config`    | `$BUBBLE_AGENT_CONFIG_FILE` or `~/.config/bubble-agent/bubble-agent.conf` |
| `--bin`             | `$BUBBLE_AGENT_BIN` or `opencode`               |
| `--workspace`       | -                                               |
| `--dry-run`         | print command only, do not execute              |

Environment variables `BUBBLE_AGENT_CONFIG_FILE` and `BUBBLE_AGENT_BIN` are still honored as fallback defaults.

Format: `type:source:destination`

Available types:

| Type            | Behavior                               |
| --------------- | -------------------------------------- |
| `bind`          | Read-write, source must exist          |
| `ro-bind`       | Read-only, source must exist           |
| `bind-try`      | Read-write, silently ignored if absent |
| `ro-bind-try`   | Read-only, silently ignored if absent  |
| `symlink`       | Create a symbolic link                 |
| `env` / `setenv`| Set an environment variable            |
| `workspace`     | Parse a `.code-workspace` JSON file    |
| `workspace-path`| Override virtual workspace directory   |

Both source and destination support `~` for `$HOME` and environment variables (`$VAR`, `${VAR}`).

### Adding Toolchains

For security, **only configured paths are accessible** inside the sandbox.
Add your toolchain and project directories to the config file:

```conf
# Toolchains
bind:~/.cargo:~/.cargo
bind:~/.bun:~/.bun

# opencode state directories
bind:~/.config/opencode:~/.config/opencode
bind:~/.cache/opencode:~/.cache/opencode
bind:~/.local/share/opencode:~/.local/share/opencode
bind:~/.local/state/opencode:~/.local/state/opencode

# Projects
bind:~/projects:~/projects
```

See `bubble-agent.example.conf` for a full list of examples.

### Virtual Workspace (`.code-workspace`)

Parse a VS Code-style `.code-workspace` JSON file to assemble a virtual workspace inside the sandbox. The agent sees all repositories as if they were under a single directory tree.

```jsonc
// ~/projects/my.code-workspace
{
  "folders": [
    {"path": "/home/user/frontend-app", "name": "frontend"},
    {"path": "/home/user/backend-api",   "name": "backend"},
    {"path": "../libs/shared-utils",   "name": "shared"}
  ]
}
```

```conf
# bubble-agent.conf
workspace:~/projects/my.code-workspace

# Custom workspace directory (default: ~/workspace)
workspace-path:~/my-virtual-workspace
```

Inside the sandbox, the agent sees:

```
~/workspace/
  frontend/  -> /home/user/frontend-app
  backend/   -> /home/user/backend-api
  shared/    -> /home/user/libs/shared-utils
```

Relative paths are resolved relative to the `.code-workspace` file's location. Duplicate folder names get a `_N` suffix appended.

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
