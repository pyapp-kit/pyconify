from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pyconify import freedesktop_theme

if TYPE_CHECKING:
    from pathlib import Path

ICONS = {
    "edit-clear": "ic:sharp-clear",
    "edit-delete": {"key": "ic:sharp-delete", "color": "red"},
    "weather-overcast": "ic:sharp-cloud",
    "bell": "bi:bell",
}


@pytest.mark.usefixtures("no_cache")
def test_freedesktop(tmp_path: Path) -> None:
    d = freedesktop_theme("mytheme", ICONS, base_directory=tmp_path, comment="asdff")
    assert d == tmp_path
    theme_dir = tmp_path / "mytheme"
    assert theme_dir.exists()
    assert theme_dir.is_dir()

    # index.theme is created
    index = theme_dir / "index.theme"
    assert index.exists()
    index_txt = index.read_text()
    assert "asdff" in index_txt
    assert "Directories=actions,other,status" in index_txt

    # files are put in their proper freedesktop subdirs
    svgs = set(theme_dir.rglob("*.svg"))
    assert theme_dir / "actions" / "edit-clear.svg" in svgs
    assert theme_dir / "status" / "weather-overcast.svg" in svgs
    assert theme_dir / "other" / "bell.svg" in svgs


@pytest.mark.usefixtures("no_cache")
def test_freedesktop_tmp_dir() -> None:
    d = freedesktop_theme("mytheme", ICONS, comment="asdff")
    assert d.exists()


@pytest.mark.usefixtures("no_cache")
@pytest.mark.parametrize("backend", ["PySide2", "PyQt5", "PyQt6", "PySide6"])
def test_freedesktop_qt(backend: str, tmp_path: Path) -> None:
    """Test that the created folder works as a Qt Theme."""
    QtGui = pytest.importorskip(f"{backend}.QtGui", reason=f"requires {backend}")

    app = QtGui.QGuiApplication([])
    d = freedesktop_theme("mytheme", ICONS, base_directory=tmp_path, comment="comment")
    assert d == tmp_path

    QtGui.QIcon.setThemeSearchPaths([str(d)])
    QtGui.QIcon.setThemeName("mytheme")
    assert QtGui.QIcon.hasThemeIcon("bell")
    assert not QtGui.QIcon.fromTheme("bell").isNull()
    assert QtGui.QIcon.hasThemeIcon("edit-clear")
    assert not QtGui.QIcon.fromTheme("edit-clear").isNull()
    assert not QtGui.QIcon.hasThemeIcon("nevvvvvver-gonna-be-there")
    app.quit()
