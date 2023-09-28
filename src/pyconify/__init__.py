"""iconify for python. Universal icon framework."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyconify")
except PackageNotFoundError:
    __version__ = "uninstalled"
__author__ = "Talley Lambert"
__email__ = "talley.lambert@gmail.com"
__all__ = ["svg", "collection", "collections", "icon_data", "search"]

from .api import collection, collections, icon_data, search, svg
