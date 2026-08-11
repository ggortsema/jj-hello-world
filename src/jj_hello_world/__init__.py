"""Reference hello-world plugin for JJ."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("jj-hello-world")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.1.0"

__all__ = ["__version__"]
