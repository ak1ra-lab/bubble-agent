# Installation

## Prerequisites

### bubblewrap

```shell
# Debian/Ubuntu
sudo apt install bubblewrap

# Fedora
sudo dnf install bubblewrap

# Arch Linux
sudo pacman -S bubblewrap

# Alpine
sudo apk add bubblewrap

# openSUSE
sudo zypper install bubblewrap
```

### Python

Python >= 3.11 is required.  [uv] is recommended for installation.

Make sure `~/.local/bin` is in your `PATH`.

## Install bubble-agent

### From PyPI

```shell
uv tool install bubble-agent
```

### From Test PyPI

```shell
uv tool install --index-url https://test.pypi.org/simple/ bubble-agent
```

### From GitHub

Install directly from the repository:

```shell
# Latest master branch
uv tool install git+https://github.com/ak1ra-lab/bubble-agent.git

# Specific branch (e.g. dev)
uv tool install git+https://github.com/ak1ra-lab/bubble-agent.git@dev

# Specific tag (e.g. v0.1.0)
uv tool install git+https://github.com/ak1ra-lab/bubble-agent.git@v0.1.0
```

### From local clone

```shell
git clone https://github.com/ak1ra-lab/bubble-agent.git
cd bubble-agent
uv tool install .
```

For development convenience, the repo includes a `justfile`:

```shell
just install    # uv tool install . + copy example config as reference
just uninstall  # uv tool uninstall bubble-agent
```

## Configuration

Create your config file from the example:

```shell
mkdir -p ~/.config/bubble-agent
curl -o ~/.config/bubble-agent/bubble-agent.conf \
  https://raw.githubusercontent.com/ak1ra-lab/bubble-agent/master/bubble-agent.example.conf
# edit ~/.config/bubble-agent/bubble-agent.conf
```

See [Configuration](configuration.md) for details.

## Uninstall

```shell
uv tool uninstall bubble-agent
```

Optionally remove the config directory:

```shell
rm -rf ~/.config/bubble-agent
```

[uv]: https://docs.astral.sh/uv/
