from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

import pyconify
from pyconify import _cache, api
from pyconify._cache import _SVGCache, clear_cache, get_cache_directory


def test_cache(tmp_path: Path) -> None:
    assert isinstance(get_cache_directory(), Path)

    # don't delete the real cache, regardless of other monkeypatching
    with patch.object(_cache, "get_cache_directory", lambda: tmp_path / "tmp"):
        clear_cache()

    cache = _SVGCache(tmp_path)
    KEY, VAL = "testkey", b"testval"
    cache[KEY] = VAL
    assert cache[KEY] == VAL
    assert cache.path.joinpath(f"{KEY}.svg").exists()
    assert list(cache) == [KEY]
    assert KEY in cache
    del cache[KEY]
    assert not cache.path.joinpath(f"{KEY}.svg").exists()

    with pytest.raises(KeyError):
        cache["not a key"]


def test_cache_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    some_path = Path("/some/path").expanduser().resolve()
    monkeypatch.setattr(_cache, "PYCONIFY_CACHE", str(some_path))
    assert get_cache_directory() == some_path


def test_delete_stale() -> None:
    cache = {"fa_0": b""}
    _cache._delete_stale_svgs(cache)
    assert not cache


@pytest.fixture
def tmp_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    cache = tmp_path / "cache"
    monkeypatch.setattr(_cache, "PYCONIFY_CACHE", str(cache))
    monkeypatch.setattr(_cache, "_SVG_CACHE", None)
    yield cache


@pytest.mark.usefixtures("tmp_cache")
def test_tmp_svg_with_fixture() -> None:
    """Test that we can set the cache directory to tmp_path with monkeypatch."""
    result3 = pyconify.svg_path("bi", "alarm-fill")
    assert str(result3).startswith(str(_cache.get_cache_directory()))


@contextmanager
def internet_offline() -> Iterator[None]:
    """Simulate an offline internet connection."""
    session = api._session()
    with patch.object(session, "get") as mock:
        mock.side_effect = requests.ConnectionError("No internet connection.")
        # clear functools caches...
        for val in vars(pyconify).values():
            if hasattr(val, "cache_clear"):
                val.cache_clear()
        yield


@pytest.mark.usefixtures("tmp_cache")
def test_cache_used_offline() -> None:
    svg = pyconify.svg_path("mdi:pen-add", color="#333333")
    svgb = pyconify.svg("mdi:pen-add", color="#333333")
    # make sure a previously cached icon works offline

    with internet_offline():
        # make sure the patch works
        with pytest.raises(requests.ConnectionError):
            pyconify.svg_path("mdi:pencil-plus-outline")

        # make sure the cached icon works
        svg2 = pyconify.svg_path("mdi:pen-add", color="#333333")
        assert svg == svg2

        svgb2 = pyconify.svg("mdi:pen-add", color="#333333")
        assert svgb == svgb2


@pytest.mark.usefixtures("tmp_cache")
def test_cache_loaded_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_cache, "_SVG_CACHE", None)
    with internet_offline():
        assert isinstance(_cache.svg_cache(), _cache._SVGCache)
