"""A Class for generating QIcons from SVGs with arbitrary colors at runtime."""
from typing import Literal

from qtpy.QtCore import QByteArray, QPoint, QRect, QRectF, Qt
from qtpy.QtGui import QIcon, QIconEngine, QImage, QPainter, QPixmap
from qtpy.QtSvg import QSvgRenderer

from pyconify.api import svg


class QIconify(QIcon):
    def __init__(
        self,
        *key: str,
        color: str | None = None,
        flip: Literal["horizontal", "vertical", "horizontal,vertical"] | None = None,
        rotate: str | int | None = None,
    ) -> None:
        if len(key) == 1:
            if ":" in key[0]:
                prefix, name = key[0].split(":")
            else:
                raise ValueError(
                    "If only one argument is passed, it must be in the format "
                    "'prefix:name'"
                )
        elif len(key) == 2:
            prefix, name = key
        else:
            raise ValueError(
                "QIconify must be initialized with either 1 or 2 arguments."
            )
        svg_bytes = svg(prefix, name, color=color, flip=flip, rotate=rotate)
        super().__init__(SVGBufferIconEngine(svg_bytes))


class SVGBufferIconEngine(QIconEngine):
    """A custom QIconEngine that can render an SVG buffer."""

    def __init__(self, xml: bytes | str | QByteArray) -> None:
        if isinstance(xml, str):
            xml = xml.encode("utf-8")
        self._data = QByteArray(xml)
        self._renderer = QSvgRenderer(self._data)
        self._renderer.setFramesPerSecond(20)
        super().__init__()

    def paint(self, painter: QPainter, rect, mode, state):
        """Paint the icon in `rect` using `painter`."""
        self._renderer.render(painter, QRectF(rect))

    def clone(self):
        """Required to subclass abstract QIconEngine."""
        return SVGBufferIconEngine(self._data)

    def pixmap(self, size, mode, state):
        """Return the icon as a pixmap with requested size, mode, and state."""
        img = QImage(size, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        pixmap = QPixmap.fromImage(img, Qt.ImageConversionFlag.NoFormatConversion)
        painter = QPainter(pixmap)
        self.paint(painter, QRect(QPoint(0, 0), size), mode, state)
        return pixmap
