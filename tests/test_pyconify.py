from pathlib import Path

import pyconify
import pytest
from pyconify import _cache


def test_collections() -> None:
    result = pyconify.collections("bi", "fa")
    assert isinstance(result, dict)
    assert set(result) == {"bi", "fa"}


def test_collection() -> None:
    result = pyconify.collection("geo", chars=True, info=True)
    assert isinstance(result, dict)
    assert result["prefix"] == "geo"

    with pytest.raises(IOError, match="Icon set 'not' not found."):
        pyconify.collection("not")


def test_icon_data() -> None:
    result = pyconify.icon_data("bi", "alarm")
    assert isinstance(result, dict)
    assert result["prefix"] == "bi"
    assert "alarm" in result["icons"]

    with pytest.raises(IOError, match="Icon set 'not' not found"):
        pyconify.icon_data("not", "found")


@pytest.mark.usefixtures("no_cache")
def test_svg() -> None:
    result = pyconify.svg("bi", "alarm", rotate=90, box=True)
    assert isinstance(result, bytes)
    assert result.startswith(b"<svg")

    with pytest.raises(IOError, match="Icon 'not:found' not found."):
        pyconify.svg("not", "found")


@pytest.mark.usefixtures("no_cache")
def test_tmp_svg(tmp_path: Path) -> None:
    result1 = pyconify.svg_path("bi", "alarm", rotate=90, box=True)
    assert isinstance(result1, Path)
    assert result1.read_bytes() == pyconify.svg("bi", "alarm", rotate=90, box=True)

    # this one shouldn't be in the cache at this point
    result2 = pyconify.svg_path("bi", "alarm", rotate=90, box=True, dir=tmp_path)
    assert isinstance(result2, Path)
    assert result2.parent == tmp_path
    assert result2 != result1
    assert result2.read_bytes() == pyconify.svg("bi", "alarm", rotate=90, box=True)


def test_tmp_svg_with_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that we can set the cache directory to tmp_path with monkeypatch."""
    monkeypatch.setattr(_cache, "PYCONIFY_CACHE", str(tmp_path))
    monkeypatch.setattr(_cache, "_SVG_CACHE", None)
    result3 = pyconify.svg_path("bi", "alarm-fill")
    assert str(result3).startswith(str(_cache.get_cache_directory()))


def test_css() -> None:
    result = pyconify.css("bi", "alarm")
    assert result.startswith(".icon--bi")

    # FIXME... this isn't returning a valid thingy
    result2 = pyconify.css(
        "bi",
        "alarm",
        selector=".test",
        common="common",
        override="override",
        pseudo=True,
        var="asdf",
        square=True,
        color="red",
        mode="mask",
        format="compact",
    )
    assert result2.startswith("common")

    with pytest.raises(IOError, match="Icon set 'not' not found."):
        pyconify.css("not:found")

    with pytest.warns(UserWarning, match=r"Icon\(s\) \['nor-this', 'not-an-icon'\]"):
        pyconify.css("bi:not-an-icon,nor-this")


def test_last_modified() -> None:
    assert isinstance(pyconify.last_modified("bi")["bi"], int)


def test_keywords() -> None:
    keywords = pyconify.keywords("home")
    assert isinstance(keywords, dict)
    assert keywords["prefix"] == "home"
    assert keywords["matches"]

    keywords = pyconify.keywords(keyword="home")
    assert keywords["keyword"] == "home"
    assert keywords["matches"]

    with pytest.warns(UserWarning, match="Cannot specify both prefix and keyword"):
        assert isinstance(pyconify.keywords("home", keyword="home"), dict)

    assert pyconify.keywords()


def test_search() -> None:
    result = pyconify.search("arrow", prefixes={"bi"}, limit=10, start=2)
    assert result["collections"]

    result = pyconify.search("arrow", prefixes="bi", category="General")
    assert result["collections"]


def test_iconify_version() -> None:
    assert isinstance(pyconify.iconify_version(), str)
