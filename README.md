# bubble-agent

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/ak1ra-lab/bubble-agent/.github%2Fworkflows%2Fpublish-to-pypi.yaml)](https://github.com/ak1ra-lab/bubble-agent/actions/workflows/publish-to-pypi.yaml)
[![PyPI - Version](https://img.shields.io/pypi/v/bubble-agent)](https://pypi.org/project/bubble-agent/)
[![Docs](https://img.shields.io/badge/docs-online-0a7ea4)](https://ak1ra-lab.github.io/bubble-agent/)

> This project is inspired by [cyunrei/opencode-bwrap](https://github.com/cyunrei/opencode-bwrap).

Run your coding agent in a bubble.

Uses [bubblewrap](https://github.com/containers/bubblewrap) to sandbox coding agents with configurable bind mounts and virtual workspace (`.code-workspace`) support.

By default, the sandbox wraps [opencode](https://github.com/anomalyco/opencode). Use `--bin` to run a different coding agent.

## Quick Start

```shell
git clone https://github.com/ak1ra-lab/bubble-agent.git
cd bubble-agent
just install

bubble-agent                              # runs opencode by default
bubble-agent ~/my-project                 # work in a specific directory
bubble-agent --dry-run                    # preview the bwrap command
```

See [Documentation](https://ak1ra-lab.github.io/bubble-agent/) for full usage, configuration, and workspace features.
