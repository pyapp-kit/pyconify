"""iconify for python. Universal icon framework."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyconify")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "uninstalled"

__author__ = "Talley Lambert"
__email__ = "talley.lambert@gmail.com"
__all__ = [
    "clear_api_cache",
    "clear_cache",
    "collection",
    "collections",
    "css",
    "freedesktop_theme",
    "get_cache_directory",
    "icon_data",
    "iconify_version",
    "keywords",
    "last_modified",
    "search",
    "set_api_cache_maxsize",
    "svg",
    "svg_path",
]

from ._cache import clear_cache, get_cache_directory
from .api import (
    clear_api_cache,
    collection,
    collections,
    css,
    icon_data,
    iconify_version,
    keywords,
    last_modified,
    search,
    set_api_cache_maxsize,
    svg,
    svg_path,
)
from .freedesktop import freedesktop_theme
