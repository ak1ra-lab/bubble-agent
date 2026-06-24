# bubble agent wrapper Makefile

PREFIX ?= $(HOME)/.local
BINDIR = $(PREFIX)/bin

SCRIPT = bubble-agent
CONFIG = bubble-agent.example.conf
CONFIG_DIR = $(HOME)/.config/bubble-agent

.PHONY: all install uninstall lint

all:
	@echo "Usage: make install [PREFIX=path]"

lint:
	ruff check --fix $(SCRIPT)
	ruff format $(SCRIPT)

install:
	mkdir -p $(BINDIR) $(CONFIG_DIR)
	install -m 755 $(SCRIPT) $(BINDIR)/$(SCRIPT)
	install -m 644 $(CONFIG) $(CONFIG_DIR)/bubble-agent.example.conf

uninstall:
	rm -f $(BINDIR)/$(SCRIPT)
	rm -f $(CONFIG_DIR)/bubble-agent.example.conf
