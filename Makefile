# bubble agent wrapper Makefile

PREFIX ?= $(HOME)/.local
BINDIR = $(PREFIX)/bin

SCRIPT = bubble-agent
BASH_SCRIPT = bubble-agent.sh
CONFIG = bubble-agent.example.conf
CONFIG_DIR = $(HOME)/.config/bubble-agent

.PHONY: all install uninstall lint lint-bash

all:
	@echo "Usage: make install [PREFIX=path]"

lint:
	ruff check --fix $(SCRIPT)
	ruff format $(SCRIPT)

lint-bash:
	shfmt -i 4 -ci -w $(BASH_SCRIPT)
	shellcheck $(BASH_SCRIPT)

install:
	mkdir -p $(BINDIR) $(CONFIG_DIR)
	install -m 755 $(SCRIPT) $(BINDIR)/$(SCRIPT)
	install -m 644 $(CONFIG) $(CONFIG_DIR)/bubble-agent.example.conf

uninstall:
	rm -f $(BINDIR)/$(SCRIPT)
	rm -f $(CONFIG_DIR)/bubble-agent.example.conf
