from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from pyconify import _cache


@pytest.fixture(autouse=True)
def no_cache() -> None:
    breakpoint()
    with TemporaryDirectory() as tmp:
        with patch.object(_cache, "get_cache_directory", lambda: Path(tmp)):
            yield
