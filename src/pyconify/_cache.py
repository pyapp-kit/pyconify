from __future__ import annotations

import os
from contextlib import suppress
from pathlib import Path
from typing import Iterator, MutableMapping

_SVG_CACHE: MutableMapping[str, bytes] | None = None
PYCONIFY_CACHE: str = os.environ.get("PYCONIFY_CACHE", "")
CACHE_DISABLED: bool = PYCONIFY_CACHE.lower() in {"0", "false", "no"}


def svg_cache() -> MutableMapping[str, bytes]:  # pragma: no cover
    """Return a cache for SVG files."""
    global _SVG_CACHE
    if _SVG_CACHE is None:
        if CACHE_DISABLED:
            _SVG_CACHE = {}
        else:
            try:
                _SVG_CACHE = _SVGCache()
            except Exception:
                _SVG_CACHE = {}
            with suppress(OSError):
                _delete_stale_svgs(_SVG_CACHE)
    return _SVG_CACHE


def clear_cache() -> None:
    """Clear the pyconify svg cache."""
    import shutil

    from .api import svg_path

    shutil.rmtree(get_cache_directory(), ignore_errors=True)
    global _SVG_CACHE
    _SVG_CACHE = None
    with suppress(AttributeError):
        svg_path.cache_clear()  # type: ignore


def get_cache_directory(app_name: str = "pyconify") -> Path:
    """Return the pyconify svg cache directory."""
    if PYCONIFY_CACHE:
        return Path(PYCONIFY_CACHE).expanduser().resolve()

    if os.name == "posix":
        return Path.home() / ".cache" / app_name
    elif os.name == "nt":
        appdata = os.environ.get("LOCALAPPDATA", "~/AppData/Local")
        return Path(appdata).expanduser() / app_name
    # Fallback to a directory in the user's home directory
    return Path.home() / f".{app_name}"  # pragma: no cover


# delimiter for the cache key
DELIM = "_"


def cache_key(args: tuple, kwargs: dict, last_modified: int | str) -> str:
    """Generate a key for the cache based on the function arguments."""
    _keys: tuple = args
    if kwargs:
        for item in sorted(kwargs.items()):
            if item[1] is not None:
                _keys += item
    _keys += (last_modified,)
    return DELIM.join(map(str, _keys))


class _SVGCache(MutableMapping[str, bytes]):
    """A simple directory cache for SVG files."""

    def __init__(self, directory: str | Path | None = None) -> None:
        super().__init__()
        if not directory:
            directory = get_cache_directory() / "svg_cache"  # pragma: no cover
        self.path = Path(directory).expanduser().resolve()
        self.path.mkdir(parents=True, exist_ok=True)
        self._extention = ".svg"

    def path_for(self, _key: str) -> Path:
        return self.path.joinpath(f"{_key}{self._extention}")

    def _svg_files(self) -> Iterator[Path]:
        yield from self.path.glob(f"*{self._extention}")

    def __setitem__(self, _key: str, _value: bytes) -> None:
        self.path_for(_key).write_bytes(_value)

    def __getitem__(self, _key: str) -> bytes:
        try:
            return self.path_for(_key).read_bytes()
        except FileNotFoundError:
            raise KeyError(_key) from None

    def __iter__(self) -> Iterator[str]:
        yield from (x.stem for x in self._svg_files())

    def __delitem__(self, _key: str) -> None:
        self.path_for(_key).unlink()

    def __len__(self) -> int:
        return len(list(self._svg_files()))

    def __contains__(self, _key: object) -> bool:
        return self.path_for(_key).exists() if isinstance(_key, str) else False


def _delete_stale_svgs(cache: MutableMapping) -> None:  # pragma: no cover
    """Remove all SVG files with an outdated last_modified date from the cache."""
    from .api import last_modified

    last_modified_dates = last_modified()
    for key in list(cache):
        with suppress(ValueError):
            prefix, *_, cached_last_mod = key.split(DELIM)
            if int(cached_last_mod) < last_modified_dates.get(prefix, 0):
                del cache[key]
