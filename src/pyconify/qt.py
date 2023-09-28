"""A Class for generating QIcons from SVGs with arbitrary colors at runtime."""
import atexit
import os
import tempfile
from contextlib import suppress
from functools import lru_cache
from typing import Literal

from qtpy.QtGui import QIcon

from pyconify.api import svg


@lru_cache(maxsize=None)
def _tmp_svg(key: tuple[str, ...], **kwargs) -> str:
    """Return a temporary SVG file with the given prefix and name."""
    svg_bytes = svg(*key, **kwargs)
    prefix = f"pyconify_{'-'.join(key)}".replace(":", "-")
    fd, name = tempfile.mkstemp(prefix=prefix, suffix=".svg")
    with os.fdopen(fd, "wb") as f:
        f.write(svg_bytes)

    print("Created", name, key, kwargs)

    @atexit.register
    def _remove_tmp_svg() -> None:
        with suppress(FileNotFoundError):
            print("Removing", name)
            os.remove(name)

    return name


class QIconify(QIcon):
    def __init__(
        self,
        *key: str,
        color: str | None = None,
        flip: Literal["horizontal", "vertical", "horizontal,vertical"] | None = None,
        rotate: str | int | None = None,
    ) -> None:
        self.path = _tmp_svg(key, color=color, flip=flip, rotate=rotate)
        super().__init__(self.path)
