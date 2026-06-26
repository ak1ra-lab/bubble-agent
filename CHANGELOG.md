# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-26

Initial release — a uv-managed Python package that launches coding agents
inside a [bubblewrap](https://github.com/containers/bubblewrap) sandbox.

### Added

- Sandbox coding agents with configurable bind mounts, network access, and
  environment isolation
- Config file (`~/.config/bubble-agent/bubble-agent.conf`) supporting
  `bind`, `ro-bind`, `bind-try`, `ro-bind-try`, `symlink`, and
  `env`/`setenv` entries
- Shell variable expansion in config paths: `~`, `$VAR`/`${VAR}`, and
  built-in vars `$UID`, `$EUID`, `$GID`, `$EGID`
- `path-prepend` and `path-append` config types for extending the sandbox
  `PATH`
- `.code-workspace` file support with symlinked folder view; preserve
  original tree structure with `--no-symlink` / `-S`
- NUL-separated `--args <fd>` mechanism for clean `ps` output
- Automatic `/etc/profile` patching to prevent login shells from resetting
  the sandbox `PATH`
- `--dry-run` / `-D` to preview the bwrap command without executing
- `--bin` / `-b` to choose the agent binary (defaults to `opencode`)
- Environment variable overrides: `BUBBLE_AGENT_CONFIG_FILE`,
  `BUBBLE_AGENT_BIN`
