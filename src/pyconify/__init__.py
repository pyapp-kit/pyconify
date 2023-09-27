"""iconify for python. Universal icon framework"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyconify")
except PackageNotFoundError:
    __version__ = "uninstalled"
__author__ = "Talley Lambert"
__email__ = "talley.lambert@gmail.com"
