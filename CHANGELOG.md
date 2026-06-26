# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Pass bwrap args via ``--args <fd>`` for clean ``ps`` output
- ``make_data_fd()`` general-purpose pipe writer for fd-based data passing
- Automatically patch ``/etc/profile`` to prevent login shells from resetting the sandbox ``PATH``

### Changed

- Switch from ``os.execvp`` to ``subprocess.run`` with ``pass_fds`` for reliable fd inheritance
- ``path-prepend`` and ``path-append`` now always merge with ``PATH``, even when an explicit ``env:PATH`` is set
- ``TERM`` defaults to ``xterm-256color`` instead of empty string
- ``USER`` falls back to ``getpass.getuser()`` when unset
- Duplicate workspace folder names get a parent-directory prefix instead of a numeric suffix

### Fixed

- Missing ``--chdir`` when launched with no positional arguments
- Directory names ending in ``.code-workspace`` no longer silently dropped
- Unhandled ``OSError`` when ``bwrap`` is not found in ``PATH``
- Double ``expand_path`` call on workspace file paths
- Unused ``ws_dest`` computation in ``no_symlink`` code path
