import logging
import os
import re
from pathlib import Path

SHELL_VARS = {
    "UID": str(os.getuid()),
    "EUID": str(os.geteuid()),
    "GID": str(os.getgid()),
    "EGID": str(os.getegid()),
}

SHELL_VAR_RE = re.compile(
    r"\$\{(UID|EUID|GID|EGID)\}|\$(UID|EUID|GID|EGID)(?![A-Za-z0-9_])"
)

UNEXPANDED_RE = re.compile(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?")

BIND_FLAG: dict[str, str] = {
    "bind": "--bind",
    "ro-bind": "--ro-bind",
    "bind-try": "--bind-try",
    "ro-bind-try": "--ro-bind-try",
    "symlink": "--symlink",
    "env": "--setenv",
    "setenv": "--setenv",
}


def expand_path(s: str) -> str:
    """Expand ``$UID``/``${EUID}``/..., ``$VAR``, ``~`` in *s*.

    Shell built-in vars (``UID``, ``EUID``, ``GID``, ``EGID``) are
    resolved from the process, then :func:`os.path.expandvars` and
    :func:`os.path.expanduser` handle the rest.
    """
    s = SHELL_VAR_RE.sub(lambda m: SHELL_VARS[m.group(1) or m.group(2)], s)
    return os.path.expandvars(os.path.expanduser(s))


def has_unexpanded(s: str) -> bool:
    """Return ``True`` if *s* appears to contain an unexpanded variable."""
    return "$" in s and UNEXPANDED_RE.search(s) is not None


def load_config(
    conf: Path,
) -> tuple[list[list[str]], list[str], list[str]]:
    """Parse a config file and return ``(bind_args, path_prepend, path_append)``.

    Lines are of the form ``type:source:destination`` (see docs for the
    full list of bind types).  ``#`` starts a comment; blank lines are
    ignored.  Returns empty lists when *conf* does not exist.
    """
    if not conf.is_file():
        return [], [], []

    logging.info("Loading binds from: %s", conf)
    logging.info("----------------------------------------")

    args: list[list[str]] = []
    path_prepend: list[str] = []
    path_append: list[str] = []
    count = 0

    for line in conf.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":", 2)
        if len(parts) < 2:
            continue

        typ = parts[0].strip()
        src = parts[1].strip()
        dst = parts[2].strip() if len(parts) > 2 else ""

        if typ in ("workspace", "workspace-path"):
            logging.warning(
                "[%s] config-based workspace is deprecated, use CLI args", typ
            )
            continue

        if typ in ("path-prepend", "path-append"):
            src = expand_path(src)
            if has_unexpanded(src):
                logging.warning("[%s] SKIP: unexpanded variable in %s", typ, src)
                continue
            logging.info("[%s] %s", typ, src)
            if typ == "path-prepend":
                path_prepend.append(src)
            else:
                path_append.append(src)
            count += 1
            continue

        flag = BIND_FLAG.get(typ)
        if not flag:
            logging.warning("Unknown bind type: %s", typ)
            continue

        src = expand_path(src)
        dst = expand_path(dst)

        if has_unexpanded(src) or has_unexpanded(dst):
            logging.warning("[%s] SKIP: unexpanded variable in %s:%s", typ, src, dst)
            continue

        if typ in ("bind", "ro-bind") and not os.path.exists(src):
            logging.warning("[%s] SKIP: %s (not found)", typ, src)
            continue

        if typ in ("env", "setenv"):
            logging.info("[env] %s=%s", src, dst)
        else:
            logging.info("[%s] %s -> %s", typ, src, dst)
        args.append([flag, src, dst])
        count += 1

    logging.info("----------------------------------------")
    logging.info("Total custom binds loaded: %d", count)
    logging.info("")
    return args, path_prepend, path_append
