# Usage

## Basic

```shell
bubble-agent                              # runs opencode by default
bubble-agent ~/my-project                 # work in a specific directory
bubble-agent ~/frontend ~/backend         # work in multiple directories
```

## Pass Arguments to Agent

```shell
bubble-agent -- serve                     # opencode subcommand
bubble-agent -- --prompt "write a test"   # opencode flags
```

## Options

| Flag                 | Default                                                                   |
| -------------------- | ------------------------------------------------------------------------- |
| `[paths...]`         | auto-bind `$PWD` if none given                                            |
| `-c`, `--config`     | `$BUBBLE_AGENT_CONFIG_FILE` or `~/.config/bubble-agent/bubble-agent.conf` |
| `-b`, `--bin`        | `$BUBBLE_AGENT_BIN` or `opencode`                                         |
| `-S`, `--no-symlink` | preserve original tree structure in workspace                             |
| `-D`, `--dry-run`    | print command only, do not execute                                        |

Environment variables `BUBBLE_AGENT_CONFIG_FILE` and `BUBBLE_AGENT_BIN` are honored as fallback defaults.

## Examples

```shell
# Use a different agent
bubble-agent --bin claude

# Use a custom config file
bubble-agent -c /path/to/custom.conf

# Dry-run: print the bwrap command without executing
bubble-agent --dry-run

# Use a .code-workspace file (flattened view with symlinks)
bubble-agent ~/projects/my.code-workspace

# Preserve original tree structure
bubble-agent -S ~/ansible.code-workspace

# Mix directories and .code-workspace files
bubble-agent ~/lib ~/my.code-workspace
```

## Shell Completion

```shell
eval "$(register-python-argcomplete bubble-agent)"
```
