import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from bubble_agent.config import (
    ensure_config_file,
    expand_path,
    get_example_config_content,
    has_unexpanded,
    load_config,
)
from bubble_agent.sandbox import fmt_bubble_cmd
from bubble_agent.workspace import parse_workspace, ws_folder_paths


class TestExpandPath:
    def test_tilde_expansion(self):
        result = expand_path("~/foo")
        assert result == str(Path.home() / "foo")

    def test_shell_var_uid(self):
        result = expand_path("/run/user/$UID")
        assert result == f"/run/user/{os.getuid()}"

    def test_shell_var_braces(self):
        result = expand_path("/run/user/${UID}")
        assert result == f"/run/user/{os.getuid()}"

    def test_env_var_expansion(self):
        with patch.dict(os.environ, {"TEST_VAR": "/custom/path"}):
            result = expand_path("$TEST_VAR/subdir")
            assert result == "/custom/path/subdir"


class TestHasUnexpanded:
    def test_no_vars(self):
        assert has_unexpanded("/plain/path") is False

    def test_unexpanded_var(self):
        assert has_unexpanded("/path/$UNKNOWN") is True

    def test_unexpanded_braces(self):
        assert has_unexpanded("/path/${UNKNOWN}") is True

    def test_dollar_without_var(self):
        assert has_unexpanded("price is $5") is False


class TestLoadConfig:
    def test_nonexistent_file(self, tmp_path):
        args, prepend, append = load_config(tmp_path / "nonexistent.conf")
        assert args == []
        assert prepend == []
        assert append == []

    def test_empty_file(self, tmp_path):
        conf = tmp_path / "empty.conf"
        conf.write_text("")
        args, prepend, append = load_config(conf)
        assert args == []

    def test_comments_and_blank_lines(self, tmp_path):
        conf = tmp_path / "test.conf"
        conf.write_text("# comment\n\n  # indented comment\n")
        args, prepend, append = load_config(conf)
        assert args == []

    def test_bind_existing_path(self, tmp_path):
        src = tmp_path / "source"
        src.mkdir()
        conf = tmp_path / "test.conf"
        conf.write_text(f"bind:{src}:{src}\n")
        args, prepend, append = load_config(conf)
        assert len(args) == 1
        assert args[0] == ["--bind", str(src), str(src)]

    def test_bind_nonexistent_skipped(self, tmp_path):
        conf = tmp_path / "test.conf"
        conf.write_text("bind:/nonexistent/path:/nonexistent/path\n")
        args, prepend, append = load_config(conf)
        assert args == []

    def test_bind_try_nonexistent_included(self, tmp_path):
        conf = tmp_path / "test.conf"
        conf.write_text("bind-try:/nonexistent/path:/nonexistent/path\n")
        args, prepend, append = load_config(conf)
        assert len(args) == 1

    def test_env_entry(self, tmp_path):
        conf = tmp_path / "test.conf"
        conf.write_text("env:FOO:bar\n")
        args, prepend, append = load_config(conf)
        assert args == [["--setenv", "FOO", "bar"]]

    def test_path_prepend(self, tmp_path):
        conf = tmp_path / "test.conf"
        conf.write_text("path-prepend:/custom/bin\n")
        args, prepend, append = load_config(conf)
        assert prepend == ["/custom/bin"]

    def test_path_append(self, tmp_path):
        conf = tmp_path / "test.conf"
        conf.write_text("path-append:/extra/bin\n")
        args, prepend, append = load_config(conf)
        assert append == ["/extra/bin"]


class TestParseWorkspace:
    def test_nonexistent_file(self):
        result = parse_workspace("/nonexistent.code-workspace", "/dest")
        assert result == []

    def test_empty_folders(self, tmp_path):
        ws = tmp_path / "test.code-workspace"
        ws.write_text(json.dumps({"folders": []}))
        result = parse_workspace(str(ws), "/dest")
        assert result == []

    def test_absolute_folder_path(self, tmp_path):
        folder = tmp_path / "project"
        folder.mkdir()
        ws = tmp_path / "test.code-workspace"
        ws.write_text(json.dumps({"folders": [{"path": str(folder)}]}))
        result = parse_workspace(str(ws), str(tmp_path / "workspace"))
        assert len(result) == 2
        assert result[0] == ["--bind-try", str(folder), str(folder)]
        assert result[1][0] == "--symlink"

    def test_relative_folder_path(self, tmp_path):
        folder = tmp_path / "project"
        folder.mkdir()
        ws = tmp_path / "test.code-workspace"
        ws.write_text(json.dumps({"folders": [{"path": "project"}]}))
        result = parse_workspace(str(ws), str(tmp_path / "workspace"))
        assert len(result) == 2

    def test_no_symlink_mode(self, tmp_path):
        folder = tmp_path / "project"
        folder.mkdir()
        ws = tmp_path / "test.code-workspace"
        ws.write_text(json.dumps({"folders": [{"path": str(folder)}]}))
        result = parse_workspace(str(ws), str(tmp_path / "workspace"), no_symlink=True)
        assert len(result) == 1
        assert result[0] == ["--bind-try", str(folder), str(folder)]


class TestWsFolderPaths:
    def test_nonexistent_file(self):
        result = ws_folder_paths("/nonexistent.code-workspace")
        assert result == []

    def test_returns_paths(self, tmp_path):
        folder = tmp_path / "project"
        folder.mkdir()
        ws = tmp_path / "test.code-workspace"
        ws.write_text(json.dumps({"folders": [{"path": str(folder)}]}))
        result = ws_folder_paths(str(ws))
        assert len(result) == 1
        assert result[0] == folder.resolve()


class TestFmtBubbleCmd:
    def test_basic_formatting(self):
        groups = [["--unshare-pid"], ["--ro-bind", "/usr", "/usr"]]
        result = fmt_bubble_cmd(groups, "/usr/bin/agent", ["--flag"])
        assert "bwrap" in result
        assert "--unshare-pid" in result
        assert "--ro-bind /usr /usr" in result
        assert "/usr/bin/agent" in result
        assert "--flag" in result
        assert "\\\n" in result


class TestDryRun:
    def test_dry_run_exits_zero(self):
        result = subprocess.run(
            [sys.executable, "-m", "bubble_agent", "--dry-run"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_dry_run_outputs_bwrap(self):
        result = subprocess.run(
            [sys.executable, "-m", "bubble_agent", "--dry-run"],
            capture_output=True,
            text=True,
        )
        assert "bwrap" in result.stderr

    def test_dry_run_with_directory(self, tmp_path):
        result = subprocess.run(
            [sys.executable, "-m", "bubble_agent", "--dry-run", str(tmp_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert str(tmp_path) in result.stderr

    def test_dry_run_with_workspace(self, tmp_path):
        folder = tmp_path / "project"
        folder.mkdir()
        ws = tmp_path / "test.code-workspace"
        ws.write_text(json.dumps({"folders": [{"path": str(folder)}]}))
        result = subprocess.run(
            [sys.executable, "-m", "bubble_agent", "--dry-run", str(ws)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert str(folder) in result.stderr


class TestEnsureConfigFile:
    def test_creates_new_file(self, tmp_path):
        conf = tmp_path / "new.conf"
        ensure_config_file(conf)
        assert conf.is_file()
        content = conf.read_text()
        assert "bubble-agent configuration file" in content

    def test_does_not_overwrite_existing(self, tmp_path):
        conf = tmp_path / "existing.conf"
        conf.write_text("custom content")
        ensure_config_file(conf)
        assert conf.read_text() == "custom content"

    def test_creates_parent_dirs(self, tmp_path):
        conf = tmp_path / "deeply" / "nested" / "dirs" / "config.conf"
        ensure_config_file(conf)
        assert conf.is_file()


class TestGetExampleConfigContent:
    def test_returns_nonempty_string(self):
        content = get_example_config_content()
        assert len(content) > 0
        assert "bubble-agent configuration file" in content
        assert "bind:" in content
