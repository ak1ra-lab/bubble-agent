import argparse
import getpass
import logging
import os
from pathlib import Path

from bubble_agent.config import expand_path, load_config
from bubble_agent.workspace import parse_workspace, ws_folder_paths


def fmt_bubble_cmd(
    groups: list[list[str]],
    bin_path: str,
    agent_args: list[str],
    *,
    extra_groups: list[list[str]] | None = None,
) -> str:
    """Format a ``bwrap`` command-line string for ``--dry-run`` output.

    Each group in *groups* is joined with spaces; groups are separated by
    `` \\\n  `` for readability.  *extra_groups* are appended after
    *groups* (useful for fd-based entries that exist in the real command
    line but are not part of *groups*).
    """
    items: list[str] = ["bwrap"]
    for g in groups:
        items.append(" ".join(g))
    if extra_groups:
        for g in extra_groups:
            items.append(" ".join(g))
    items.append("--")
    items.append(bin_path)
    items.extend(agent_args)
    return " \\\n  ".join(items)


def make_data_fd(data: bytes) -> int:
    """Write *data* into a pipe and return the read-end file descriptor.

    Uses ``os.pipe2(0)`` to avoid ``FD_CLOEXEC`` so the fd survives
    ``os.execvp``.  The caller is responsible for closing the returned fd
    (the kernel will close any leaked fd automatically on process exit).
    """
    r_fd, w_fd = os.pipe2(0)
    try:
        while data:
            try:
                n = os.write(w_fd, data)
            except InterruptedError:
                continue
            data = data[n:]
    finally:
        os.close(w_fd)
    return r_fd


def patch_etc_profile(custom_path: str) -> bytes:
    """Return a patched ``/etc/profile`` that keeps *custom_path* in effect.

    The original content is preserved as-is; *custom_path* is appended at
    the end so its ``PATH`` assignment always wins over any earlier
    assignments within the same file.
    """
    try:
        original = Path("/etc/profile").read_text()
    except OSError:
        original = ""
    patched = original.rstrip("\n") + f'\nPATH="{custom_path}"\nexport PATH\n'
    return patched.encode()


def resolv_conf_args() -> list[list[str]]:
    """Bind-resolve ``/etc/resolv.conf`` when it is a symlink.

    Returns the ``--ro-bind`` entry for the parent directory of the
    symlink target, or an empty list when nothing needs to be done.
    """
    resolv = Path("/etc/resolv.conf")
    if not resolv.is_symlink():
        return []
    try:
        real = resolv.resolve(strict=True)
    except OSError:
        return []
    if real.parent.is_dir():
        logging.info("resolv.conf symlink: /etc/resolv.conf -> %s", real)
        return [["--ro-bind", str(real.parent), str(real.parent)]]
    return []


def build_bubble_args(opts: argparse.Namespace) -> list[list[str]]:
    """Build the full list of bwrap argument groups from CLI *opts*.

    Combines fixed sandbox setup (namespaces, mounts, env vars) with
    entries from the config file and positional path arguments.
    """
    home = os.environ.get("HOME", str(Path.home()))
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or getpass.getuser()
    logname = os.environ.get("LOGNAME") or user
    shell = os.environ.get("SHELL", "/bin/sh")
    uid = os.getuid()

    args: list[list[str]] = []

    args.append(["--unshare-pid"])
    args.append(["--die-with-parent"])
    args.append(["--new-session"])

    args.append(["--clearenv"])
    args.extend(
        [
            ["--setenv", "HOME", home],
            ["--setenv", "USER", user],
            ["--setenv", "LOGNAME", logname],
            ["--setenv", "TERM", os.environ.get("TERM", "xterm-256color")],
            ["--setenv", "LANG", os.environ.get("LANG", "en_US.UTF-8")],
            ["--setenv", "SHELL", shell],
        ]
    )

    args.append(["--share-net"])
    args.append(["--dev", "/dev"])

    args.extend(
        [
            ["--ro-bind", "/usr", "/usr"],
            ["--ro-bind", "/etc", "/etc"],
            ["--ro-bind-try", "/lib", "/lib"],
            ["--ro-bind-try", "/lib64", "/lib64"],
            ["--ro-bind-try", "/lib32", "/lib32"],
            ["--ro-bind-try", "/sys", "/sys"],
        ]
    )

    args.append(["--symlink", "usr/bin", "/bin"])
    args.append(["--symlink", "usr/sbin", "/sbin"])

    args.append(["--proc", "/proc"])
    args.append(["--tmpfs", "/tmp"])

    args.append(["--tmpfs", "/run"])
    args.append(["--dir", f"/run/user/{uid}"])
    args.append(["--setenv", "XDG_RUNTIME_DIR", f"/run/user/{uid}"])

    args.append(["--dir", "/var"])
    args.append(["--symlink", "../tmp", "var/tmp"])

    args.extend(resolv_conf_args())

    config_groups, path_prepend, path_append = load_config(opts.config)

    explicit_path = next(
        (
            g[2]
            for g in reversed(config_groups)
            if g[0] == "--setenv" and g[1] == "PATH"
        ),
        None,
    )

    if explicit_path is not None:
        config_groups = [
            g for g in config_groups if not (g[0] == "--setenv" and g[1] == "PATH")
        ]
        base_parts = explicit_path.split(":") if explicit_path else []
        all_paths = list(path_prepend) + base_parts + list(path_append)
    else:
        base_path = os.environ.get("PATH", "")
        all_paths = (
            list(path_prepend)
            + (base_path.split(":") if base_path else [])
            + list(path_append)
        )

    seen: set[str] = set()
    merged: list[str] = []
    for p in all_paths:
        if p and p not in seen:
            seen.add(p)
            merged.append(p)
    path_value = ":".join(merged)
    args.append(["--setenv", "PATH", path_value])

    args.extend(config_groups)

    dir_paths: list[str] = []
    ws_files: list[str] = []

    for p in opts.paths or []:
        expanded = os.path.abspath(expand_path(p))
        if expanded.endswith(".code-workspace"):
            if os.path.isfile(expanded):
                ws_files.append(expanded)
            else:
                logging.warning(
                    "[path] %s looks like a workspace file but "
                    "is not a regular file, treating as directory",
                    expanded,
                )
                dir_paths.append(expanded)
        else:
            dir_paths.append(expanded)

    for dp in dir_paths:
        args.append(["--bind-try", dp, dp])

    if ws_files:
        if opts.no_symlink:
            for ws in ws_files:
                args.extend(parse_workspace(ws, "", no_symlink=True))
            args.append(["--dir", home])

            all_folders: list[Path] = []
            for ws in ws_files:
                all_folders.extend(ws_folder_paths(ws))
            chdir = (
                os.path.commonpath([str(f) for f in all_folders])
                if all_folders
                else str(Path(ws_files[0]).parent)
            )
            args.append(["--chdir", chdir])
        else:
            ws_dest = expand_path("~/workspace")
            args.append(["--tmpfs", ws_dest])
            args.append(["--dir", home])
            for ws in ws_files:
                args.extend(parse_workspace(ws, ws_dest))
            args.append(["--chdir", ws_dest])
    elif dir_paths:
        args.append(["--dir", home])
        args.append(["--chdir", dir_paths[0]])
        if opts.no_symlink:
            logging.warning("--no-symlink has no effect without a .code-workspace file")
    else:
        pwd = str(Path.cwd())
        args.append(["--dir", home])
        args.append(["--bind", pwd, pwd])
        args.append(["--chdir", pwd])
        logging.info("[pwd] auto-binding cwd: %s", pwd)

    return args
