from pathlib import Path
from typing import Iterator

import pytest
from pyconify import get_cache_directory


@pytest.fixture(autouse=True, scope="session")
def ensure_no_cache() -> Iterator[None]:
    """Ensure that tests don't modify the user cache."""
    cache_dir = Path(get_cache_directory())
    exists = cache_dir.exists()
    if exists:
        # get hash of cache directory
        cache_hash = hash(tuple(cache_dir.rglob("*")))
    try:
        yield
    finally:
        assert cache_dir.exists() == exists, "Cache directory was created or deleted"
        if exists and cache_hash != hash(tuple(cache_dir.rglob("*"))):
            raise AssertionError("User Cache directory was modified")
