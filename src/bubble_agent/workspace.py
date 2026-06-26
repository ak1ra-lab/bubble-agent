import json
import logging
from pathlib import Path

from bubble_agent.config import expand_path


def parse_workspace(
    ws_file: str, dest: str, *, no_symlink: bool = False
) -> list[list[str]]:
    f = Path(ws_file)
    if not f.is_file():
        logging.warning("Workspace file not found: %s", f)
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logging.warning("Failed to parse workspace file %s: %s", f, exc)
        return []
    folders = data.get("folders")
    if not folders:
        logging.warning("Workspace file %s has no 'folders'", f)
        return []

    ws_root = Path(expand_path(dest)) if dest else Path()
    result: list[list[str]] = []

    seen: set[str] = set()
    for folder in folders:
        raw = folder.get("path", "")
        if not raw:
            continue
        path = Path(raw)
        if not path.is_absolute():
            path = f.parent / path
        real = path.expanduser().resolve()
        if no_symlink:
            logging.info("[workspace] %s (no-symlink)", real)
            result.append(["--bind-try", str(real), str(real)])
            continue
        name = folder.get("name") or real.name
        if name in seen:
            parent_name = real.parent.name or "root"
            name = f"{parent_name}_{name}"
            if name in seen:
                suffix = 2
                while f"{name}_{suffix}" in seen:
                    suffix += 1
                name = f"{name}_{suffix}"
        seen.add(name)
        logging.info("[workspace] %s -> %s/%s", real, ws_root, name)
        result.append(["--bind-try", str(real), str(real)])
        result.append(["--symlink", str(real), f"{ws_root}/{name}"])
    return result


def ws_folder_paths(ws_file: str) -> list[Path]:
    f = Path(ws_file)
    if not f.is_file():
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    folders = data.get("folders")
    if not folders:
        return []
    result: list[Path] = []
    for folder in folders:
        raw = folder.get("path", "")
        if not raw:
            continue
        path = Path(raw)
        if not path.is_absolute():
            path = f.parent / path
        result.append(path.expanduser().resolve())
    return result
