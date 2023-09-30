from pathlib import Path
from unittest.mock import patch

import pytest
from pyconify import _cache
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
