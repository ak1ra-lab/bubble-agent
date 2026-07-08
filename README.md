# bubble-agent

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/ak1ra-lab/bubble-agent/.github%2Fworkflows%2Fpublish-to-pypi.yaml)](https://github.com/ak1ra-lab/bubble-agent/actions/workflows/publish-to-pypi.yaml)
[![PyPI - Version](https://img.shields.io/pypi/v/bubble-agent)](https://pypi.org/project/bubble-agent/)
[![PyPI - Version](https://img.shields.io/pypi/v/bubble-agent?label=test-pypi&pypiBaseUrl=https%3A%2F%2Ftest.pypi.org)](https://test.pypi.org/project/bubble-agent/)
[![Docs](https://img.shields.io/badge/docs-online-0a7ea4)](https://ak1ra-lab.github.io/bubble-agent/)

> This project is inspired by [cyunrei/opencode-bwrap](https://github.com/cyunrei/opencode-bwrap).

Run your coding agent in a bubble.

Uses [bubblewrap](https://github.com/containers/bubblewrap) to sandbox coding agents with configurable bind mounts and virtual workspace (`.code-workspace`) support.  Sandbox arguments are passed via ``--args <fd>`` for clean process listings, and ``/etc/profile`` is automatically patched to prevent login shells from resetting the custom ``PATH``.

By default, the sandbox wraps [opencode](https://github.com/anomalyco/opencode). Use `--bin` to run a different coding agent.

## Quick Start

Install with [uv]:

```shell
# From PyPI
uv tool install bubble-agent

# From Test PyPI
uv tool install --index-url https://test.pypi.org/simple/ bubble-agent

# From GitHub (master branch)
uv tool install git+https://github.com/ak1ra-lab/bubble-agent.git

# From GitHub (specific branch or tag)
uv tool install git+https://github.com/ak1ra-lab/bubble-agent.git@dev
uv tool install git+https://github.com/ak1ra-lab/bubble-agent.git@v0.1.0

# From local clone
git clone https://github.com/ak1ra-lab/bubble-agent.git
cd bubble-agent
uv tool install .
```

Then run:

```shell
bubble-agent                              # runs opencode by default
bubble-agent ~/my-project                 # work in a specific directory
bubble-agent --dry-run                    # preview the bwrap command
```

A default [configuration](https://ak1ra-lab.github.io/bubble-agent/configuration/) is
auto-created at `~/.config/bubble-agent/bubble-agent.conf` on first run — just run
`bubble-agent` and then edit the file to customize.

See [Documentation](https://ak1ra-lab.github.io/bubble-agent/) for full usage, configuration, and workspace features.

[uv]: https://docs.astral.sh/uv/
