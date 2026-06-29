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
from bubble_agent.sandbox import (
    build_bubble_args,
    fmt_bubble_cmd,
    make_data_fd,
    patch_etc_profile,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stderr,
)


def create_parser(
    default_config: Path | None = None,
    default_bin: str = "opencode",
) -> argparse.ArgumentParser:
    """Build the argument parser.

    *default_config* and *default_bin* can be overridden via environment
    variables ``BUBBLE_AGENT_CONFIG_FILE`` and ``BUBBLE_AGENT_BIN``.
    """
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
    """Split *argv* at ``--`` into bubble-agent options and agent args.

    Everything before ``--`` is parsed by :func:`create_parser`; everything
    after is forwarded to the agent binary unchanged.
    """
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


def _launch(args: list[list[str]], bin_path: str, agent_args: list[str]) -> None:
    """Feed bwrap options via ``--args <fd>`` and execute the sandbox.

    Serializes *args* into a NUL-separated pipe for ``--args <fd>``,
    patches ``/etc/profile`` to preserve the sandbox ``PATH``, and runs
    bwrap via :func:`subprocess.run` with explicit ``pass_fds``.

    Does not return — calls :func:`sys.exit` with bwrap's exit code.
    """
    bwrap_payload = [item for group in args for item in group]
    args_data = b"\0".join(a.encode("utf-8") for a in bwrap_payload) + b"\0"
    args_fd = make_data_fd(args_data)

    path_value = next(
        (g[2] for g in reversed(args) if g[0] == "--setenv" and g[1] == "PATH"),
        os.environ.get("PATH", ""),
    )
    profile_fd = make_data_fd(patch_etc_profile(path_value))

    bubble_cmd = [
        "bwrap",
        "--args",
        str(args_fd),
        "--ro-bind-data",
        str(profile_fd),
        "/etc/profile",
        "--",
        bin_path,
    ] + agent_args

    try:
        result = subprocess.run(bubble_cmd, pass_fds=[args_fd, profile_fd])
    except FileNotFoundError:
        logging.error("bwrap not found in PATH")
        sys.exit(1)
    finally:
        os.close(args_fd)
        os.close(profile_fd)

    sys.exit(result.returncode)


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point: parse CLI, build sandbox, and launch the agent.

    On ``--dry-run``, prints the equivalent ``bwrap`` command to stderr and
    exits.  Otherwise, serializes sandbox configuration into anonymous pipes
    and delegates execution to :func:`_launch`.
    """
    if argv is None:
        argv = sys.argv[1:]

    opts, agent_args = parse_cli(list(argv))
    bin_path = shutil.which(opts.bin) or opts.bin

    args = build_bubble_args(opts)

    if opts.dry_run:
        path_value = next(
            (g[2] for g in reversed(args) if g[0] == "--setenv" and g[1] == "PATH"),
            os.environ.get("PATH", ""),
        )
        extra_groups = [["--ro-bind-data", "<patched:/etc/profile>", "/etc/profile"]]
        logging.info(
            "%s\n# patched:/etc/profile sets PATH=%s",
            fmt_bubble_cmd(args, bin_path, agent_args, extra_groups=extra_groups),
            path_value,
        )
        sys.exit(0)

    _launch(args, bin_path, agent_args)
