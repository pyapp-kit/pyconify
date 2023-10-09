import shutil
from pathlib import Path
from typing import Iterator
from unittest.mock import patch

import pytest
from pyconify import _cache, api, get_cache_directory


@pytest.fixture
def no_cache(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    tmp = tmp_path_factory.mktemp("pyconify")
    TEST_CACHE = _cache._SVGCache(directory=tmp)
    with patch.object(api, "svg_cache", lambda: TEST_CACHE):
        yield


@pytest.fixture(autouse=True)
def ensure_no_cache() -> Iterator[None]:
    """Ensure that tests don't modify the user cache."""
    cache_dir = Path(get_cache_directory())
    existed = cache_dir.exists()
    if existed:
        # get hash of cache directory
        cache_hash = hash(tuple(cache_dir.rglob("*")))
    try:
        yield
    finally:
        if existed:
            assert cache_dir.exists() == existed, "Cache directory was deleted"
            if cache_hash != hash(tuple(cache_dir.rglob("*"))):
                raise AssertionError("User Cache directory was modified")
        elif cache_dir.exists():
            shutil.rmtree(cache_dir, ignore_errors=True)
            raise AssertionError("Cache directory was created outside of test fixtures")
