from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bubble-agent")
except PackageNotFoundError:
    __version__ = "0.0.0"
