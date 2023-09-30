from typing import Iterator
from unittest.mock import patch

import pytest
from pyconify import _cache, api


@pytest.fixture(autouse=True, scope="session")
def no_cache(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    tmp = tmp_path_factory.mktemp("pyconify")
    TEST_CACHE = _cache._SVGCache(directory=tmp)
    with patch.object(api, "svg_cache", lambda: TEST_CACHE):
        yield
