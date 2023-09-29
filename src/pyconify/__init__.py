"""iconify for python. Universal icon framework."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyconify")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "uninstalled"
__author__ = "Talley Lambert"
__email__ = "talley.lambert@gmail.com"
__all__ = [
    "collection",
    "collections",
    "css",
    "icon_data",
    "iconify_version",
    "keywords",
    "last_modified",
    "search",
    "svg",
    "temp_svg",
]

from .api import (
    collection,
    collections,
    css,
    icon_data,
    iconify_version,
    keywords,
    last_modified,
    search,
    svg,
    temp_svg,
)
