from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, MutableMapping

_SVG_CACHE: MutableMapping[str, bytes] | None = None


def svg_cache() -> MutableMapping[str, bytes]:  # pragma: no cover
    """Return a cache for SVG files."""
    global _SVG_CACHE
    if _SVG_CACHE is None:
        try:
            _SVG_CACHE = _SVGCache()
        except Exception:
            _SVG_CACHE = {}
    return _SVG_CACHE


def clear_cache() -> None:
    """Clear the pyconify svg cache."""
    import shutil

    shutil.rmtree(get_cache_directory(), ignore_errors=True)
    global _SVG_CACHE
    _SVG_CACHE = None


def get_cache_directory(app_name: str = "pyconify") -> Path:
    """Return the pyconify svg cache directory."""
    if os.name == "posix":
        return Path.home() / ".cache" / app_name
    elif os.name == "nt":
        appdata = os.environ.get("LOCALAPPDATA", "~/AppData/Local")
        return Path(appdata).expanduser() / app_name
    # Fallback to a directory in the user's home directory
    return Path.home() / f".{app_name}"  # pragma: no cover


def cache_key(args: tuple, kwargs: dict) -> str:
    """Generate a key for the cache based on the function arguments."""
    _keys: tuple = args
    if kwargs:
        for item in sorted(kwargs.items()):
            if item[1] is not None:
                _keys += item
    return "-".join(map(str, _keys))


class _SVGCache(MutableMapping[str, bytes]):
    """A simple directory cache for SVG files."""

    def __init__(self, directory: str | Path | None = None) -> None:
        super().__init__()
        if not directory:
            directory = get_cache_directory() / "svg_cache"  # pragma: no cover
        self.path = Path(directory).expanduser().resolve()
        self.path.mkdir(parents=True, exist_ok=True)
        self._extention = ".svg"

    def __setitem__(self, _key: str, _value: bytes) -> None:
        self.path.joinpath(f"{_key}{self._extention}").write_bytes(_value)

    def __getitem__(self, _key: str) -> bytes:
        try:
            return self.path.joinpath(f"{_key}{self._extention}").read_bytes()
        except FileNotFoundError:
            raise KeyError(_key) from None

    def __iter__(self) -> Iterator[str]:
        yield from (x.stem for x in self.path.glob(f"*{self._extention}"))

    def __delitem__(self, _key: str) -> None:
        self.path.joinpath(f"{_key}{self._extention}").unlink()

    def __len__(self) -> int:
        return len(list(self.path.glob("*{self._extention}")))

    def __contains__(self, _key: object) -> bool:
        return self.path.joinpath(f"{_key}{self._extention}").exists()
