# PYTHON_ARGCOMPLETE_OK

import argparse
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

import argcomplete

from bubble_agent import __version__
from bubble_agent.sandbox import build_bubble_args, fmt_bubble_cmd, make_data_fd

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stderr,
)


def create_parser(
    default_config: Path | None = None,
    default_bin: str = "opencode",
) -> argparse.ArgumentParser:
    if default_config is None:
        default_config = Path(
            os.environ.get(
                "BUBBLE_AGENT_CONFIG_FILE",
                "~/.config/bubble-agent/bubble-agent.conf",
            )
        ).expanduser()

    parser = argparse.ArgumentParser(
        description="Run your coding agent in a bubble.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Directories or .code-workspace files to bind into the sandbox",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=default_config,
        help="Path to config file (default: %(default)s)",
    )
    parser.add_argument(
        "-b",
        "--bin",
        default=default_bin,
        help="Agent binary to run (default: %(default)s)",
    )
    parser.add_argument(
        "-S",
        "--no-symlink",
        action="store_true",
        help="Do not symlink workspace folders (preserve original tree structure)",
    )
    parser.add_argument(
        "-D",
        "--dry-run",
        action="store_true",
        help="Print bwrap command without executing",
    )
    return parser


def parse_cli(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    try:
        split_idx = argv.index("--")
    except ValueError:
        split_idx = len(argv)

    cli_args = argv[:split_idx]
    agent_args = argv[split_idx + 1 :] if split_idx < len(argv) else []

    default_config = Path(
        os.environ.get(
            "BUBBLE_AGENT_CONFIG_FILE",
            "~/.config/bubble-agent/bubble-agent.conf",
        )
    ).expanduser()
    default_bin = os.environ.get("BUBBLE_AGENT_BIN", "opencode")

    parser = create_parser(default_config, default_bin)
    argcomplete.autocomplete(parser)
    opts = parser.parse_args(cli_args)
    return opts, agent_args


def main(argv: Sequence[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    opts, agent_args = parse_cli(list(argv))
    bin_path = shutil.which(opts.bin) or opts.bin

    args = build_bubble_args(opts)

    if opts.dry_run:
        logging.info(fmt_bubble_cmd(args, bin_path, agent_args))
        sys.exit(0)

    bwrap_payload = [item for group in args for item in group]
    data = b"\0".join(a.encode("utf-8") for a in bwrap_payload) + b"\0"
    r_fd = make_data_fd(data)

    bubble_cmd = ["bwrap", "--args", str(r_fd), "--", bin_path] + agent_args

    try:
        result = subprocess.run(bubble_cmd, pass_fds=[r_fd])
    except FileNotFoundError:
        logging.error("bwrap not found in PATH")
        sys.exit(1)
    finally:
        os.close(r_fd)

    sys.exit(result.returncode)
