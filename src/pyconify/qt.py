from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from qtpy.QtGui import QIcon

from pyconify.api import temp_svg

if TYPE_CHECKING:
    Rotation = Literal["90", "180", "270", 90, 180, 270, "-90", 1, 2, 3]


class QIconify(QIcon):
    """QIcon from Iconify API."""

    def __init__(
        self,
        *key: str,
        color: str | None = None,
        flip: Literal["horizontal", "vertical", "horizontal,vertical"] | None = None,
        rotate: Rotation | None = None,
    ) -> None:
        self.path = temp_svg(*key, color=color, flip=flip, rotate=rotate)
        super().__init__(self.path)
