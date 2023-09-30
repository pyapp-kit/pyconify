from typing import Iterator
from unittest.mock import patch

import pytest
from pyconify import api


@pytest.fixture(autouse=True, scope="session")
def no_cache() -> Iterator[None]:
    TEST_CACHE: dict = {}
    with patch.object(api, "svg_cache", lambda: TEST_CACHE):
        yield
    assert TEST_CACHE
