from pathlib import Path

import pytest
from pyconify._cache import _SVGCache, clear_cache, get_cache_directory


def test_cache(tmp_path) -> None:
    assert isinstance(get_cache_directory(), Path)
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
