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

Python >= 3.11 is required.

## From Source

```shell
git clone https://github.com/ak1ra-lab/bubble-agent.git
cd bubble-agent
just install
```

Make sure `~/.local/bin` is in your `PATH`.

## Uninstall

```shell
just uninstall
```

Optionally remove the config directory:

```shell
rm -rf ~/.config/bubble-agent
```
