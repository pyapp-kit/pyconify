from __future__ import annotations

import os
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterator, MutableMapping, TypeVar

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    P = ParamSpec("P")
    R = TypeVar("R")


def get_cache_directory(app_name: str = "pyconify") -> Path:
    if os.name == "posix":
        # Unix-based systems
        cache_dir = os.path.expanduser(f"~/.cache/{app_name}")
    elif os.name == "nt" and (local_app_data := os.environ.get("LOCALAPPDATA")):
        # Windows
        cache_dir = os.path.join(local_app_data, app_name)
    # Fallback to a directory in the user's home directory
    else:
        cache_dir = os.path.expanduser(f"~/.{app_name}")

    cache_path = Path(cache_dir)
    if not cache_path.exists():
        cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path


class SVGCache(MutableMapping[str, bytes]):
    def __init__(self, directory: str | Path | None = None) -> None:
        super().__init__()
        if not directory:
            directory = get_cache_directory() / "svg_cache"
        self._dir = Path(directory).expanduser().resolve()
        self._dir.mkdir(parents=True, exist_ok=True)

    def __setitem__(self, _key: str, _value: bytes) -> None:
        self._dir.joinpath(f"{_key}.svg").write_bytes(_value)

    def __getitem__(self, _key: str) -> bytes:
        try:
            return self._dir.joinpath(f"{_key}.svg").read_bytes()
        except FileNotFoundError:
            raise KeyError(_key) from None

    def __iter__(self) -> Iterator[str]:
        return map(str, self._dir.glob("*.svg"))

    def __delitem__(self, _key: str) -> None:
        self._dir.joinpath(f"{_key}.svg").unlink()

    def __len__(self) -> int:
        return len(list(self._dir.glob("*.svg")))

    def __contains__(self, _key: object) -> bool:
        return self._dir.joinpath(f"{_key}.svg").exists()


def svg_cache(f: Callable[P, bytes]) -> Callable[P, bytes]:
    try:
        SVG_DB: MutableMapping[str, bytes] = SVGCache()
    except OSError:
        SVG_DB = {}

    @wraps(f)
    def _inner(*args: P.args, **kwargs: P.kwargs) -> bytes:
        _keys: tuple = args
        if kwargs:
            for item in sorted(kwargs.items()):
                if item[1] is not None:
                    _keys += item
        key = "-".join(map(str, _keys))
        if key not in SVG_DB:
            SVG_DB[key] = result = f(*args, **kwargs)
            return result
        return SVG_DB[key]

    return _inner
