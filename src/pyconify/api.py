from __future__ import annotations

import atexit
import os
import tempfile
from contextlib import suppress
from functools import lru_cache
from logging import warn
from typing import TYPE_CHECKING, Literal, Sequence

import requests

if TYPE_CHECKING:
    from .types import (
        APIv2CollectionResponse,
        APIv2SearchResponse,
        APIv3KeywordsResponse,
        APIv3LastModifiedResponse,
        IconifyInfo,
        IconifyJSON,
        Rotation,
    )


def _split_prefix_name(key: tuple[str, ...]) -> tuple[str, str]:
    if len(key) == 1:
        if ":" in key[0]:
            return tuple(key[0].split(":", maxsplit=1))  # type: ignore
        else:
            raise ValueError(
                "If only one argument is passed, it must be in the format "
                f"'prefix:name'. got {key[0]!r}"
            )
    elif len(key) == 2:
        return key  # type: ignore
    else:
        raise ValueError("QIconify must be initialized with either 1 or 2 arguments.")


ROOT = "https://api.iconify.design"


@lru_cache(maxsize=None)
def collections(*prefixes: str) -> dict[str, IconifyInfo]:
    """Return collections where key is icon set prefix, value is IconifyInfo object.

    Parameters
    ----------
    prefix : str, optional
        Icon set prefix if you want to get the result only for one icon set.
        If None, return all collections.
    prefixes : Sequence[str], optional
        Comma separated list of icon set prefixes. You can use partial prefixes that
        end with "-", such as "mdi-" matches "mdi-light".
    """
    query_params = {"prefixes": ",".join(prefixes)}
    req = requests.get(f"{ROOT}/collections", params=query_params)
    req.raise_for_status()
    return req.json()  # type: ignore


@lru_cache(maxsize=None)
def collection(
    prefix: str,
    info: bool = False,
    chars: bool = False,
) -> APIv2CollectionResponse:
    """Return a list of icons in an icon set.

    Parameters
    ----------
    prefix : str
        Icon set prefix.
    info : bool, optional
        If enabled, the response will include icon set information.
    chars : bool, optional
        If enabled, the response will include the character map. The character map
        exists only in icon sets that were imported from icon fonts.
    """
    # https://api.iconify.design/collection?prefix=line-md&pretty=1
    query_params = {}
    if chars:
        query_params["chars"] = 1
    if info:
        query_params["info"] = 1
    req = requests.get(f"{ROOT}/collection?prefix={prefix}", params=query_params)
    req.raise_for_status()
    if (content := req.json()) == 404:
        raise ValueError(f"Icon set {prefix} not found.")
    return content  # type: ignore


@lru_cache(maxsize=None)
def last_modified(*prefixes: str) -> APIv3LastModifiedResponse:
    """Return last modified date for icon sets.

    Parameters
    ----------
    prefixes : Sequence[str], optional
        Comma separated list of icon set prefixes. You can use partial prefixes that
        end with "-", such as "mdi-" matches "mdi-light".  If None, return all
        collections.
    """
    # https://api.iconify.design/last-modified?prefixes=mdi,mdi-light,tabler
    query_params = {"prefixes": ",".join(prefixes)}
    req = requests.get(f"{ROOT}/last-modified", params=query_params)
    req.raise_for_status()
    return req.json()  # type: ignore


@lru_cache(maxsize=None)
def svg(
    *key: str,
    color: str | None = None,
    height: str | int | None = None,
    width: str | int | None = None,
    flip: Literal["horizontal", "vertical", "horizontal,vertical"] | None = None,
    rotate: Rotation | None = None,
    box: bool = False,
) -> bytes:
    """Generate SVG for icon.

    Returns a bytes object containing the SVG data: `b'<svg>...</svg>'`

    Example:
    https://api.iconify.design/fluent-emoji-flat/alarm-clock.svg?height=48&width=48

    Parameters
    ----------
    key: str
        Icon set prefix and name. May be passed as a single string in the format
        `"prefix:name"` or as two separate strings: `'prefix', 'name'`.
    color : str, optional
        Icon color. Replaces currentColor with specific color, resulting in icon with
        hardcoded palette.
    height : str | int, optional
        Icon height. If only one dimension is specified, such as height, other
        dimension will be automatically set to match it.
    width : str | int, optional
        Icon width. If only one dimension is specified, such as height, other
        dimension will be automatically set to match it.
    flip : str, optional
        Flip icon.
    rotate : str | int, optional
        Rotate icon. If an integer is provided, it is assumed to be in degrees.
    box : bool, optional
        Adds an empty rectangle to SVG that matches the icon's viewBox. It is needed
        when importing SVG to various UI design tools that ignore viewBox. Those tools,
        such as Sketch, create layer groups that automatically resize to fit content.
        Icons usually have empty pixels around icon, so such software crops those empty
        pixels and icon's group ends up being smaller than actual icon, making it harder
        to align it in design.
    """
    prefix, name = _split_prefix_name(key)
    if rotate not in (None, 1, 2, 3):
        rotate = str(rotate).replace("deg", "") + "deg"  # type: ignore
    query_params = {
        "color": color,
        "height": height,
        "width": width,
        "flip": flip,
        "rotate": rotate,
    }
    if box:
        query_params["box"] = 1
    req = requests.get(f"{ROOT}/{prefix}/{name}.svg", params=query_params)
    req.raise_for_status()
    return req.content


@lru_cache(maxsize=None)
def temp_svg(
    *key: str,
    color: str | None = None,
    height: str | int | None = None,
    width: str | int | None = None,
    flip: Literal["horizontal", "vertical", "horizontal,vertical"] | None = None,
    rotate: Rotation | None = None,
    box: bool = False,
    prefix=None,
    dir=None,
) -> str:
    """Create a temporary SVG file for `key` for the duration of the session."""
    svg_bytes = svg(
        *key, color=color, height=height, width=width, flip=flip, rotate=rotate, box=box
    )

    if not prefix:
        prefix = f"pyconify_{'-'.join(key)}".replace(":", "-")

    fd, tmp_name = tempfile.mkstemp(prefix=prefix, suffix=".svg", dir=dir)
    with os.fdopen(fd, "wb") as f:
        f.write(svg_bytes)

    @atexit.register
    def _remove_tmp_svg() -> None:
        with suppress(FileNotFoundError):
            os.remove(tmp_name)

    return tmp_name


@lru_cache(maxsize=None)
def css(prefix: str, *icons: str) -> str:
    # iconSelector or selector. Selector for icon, defaults to ".icon--{prefix}--{name}". Variable "{prefix}" is replaced with icon set prefix, "{name}" with icon name.
    # commonSelector or common. Common selector for icons, defaults to ".icon--{prefix}". Set it to empty to disable common code (see one of examples below). Variable "{prefix}" is replaced with icon set prefix.
    # overrideSelector or override. Selector that mixes iconSelector and commonSelector to generate icon specific style that overrides common style. See below. Default value is ".icon--{prefix}.icon--{prefix}--{name}".
    # pseudoSelector or pseudo, boolean. Set it to true if selector for icon is a pseudo-selector, such as ".icon--{prefix}--{name}::after".
    # varName or var. Name for variable to use for icon, defaults to "svg" for monotone icons, null for icons with palette. Set to null to disable.
    # forceSquare or square, boolean. Forces icon to have width of 1em.
    # color. Sets color for monotone icons. Also renders icons as background images.
    # mode: "mask" or "background". Forces icon to render as mask image or background image. If not set, mode will be detected from icon content: icons that contain currentColor will be rendered as mask image, other icons as background image.
    # format. Stylesheet formatting option. Matches options used in Sass. Supported values: "expanded", "compact", "compressed".

    # /mdi.css?icons=account-box,account-cash,account,home
    req = requests.get(f"{ROOT}/{prefix}.css?icons={','.join(icons)}")
    req.raise_for_status()
    return req.text


def icon_data(prefix: str, *names: str) -> IconifyJSON:
    """Return icon data for `names` in `prefix`.

    Example:
    https://api.iconify.design/mdi.json?icons=acount-box,account-cash,account,home

    Missing icons are added to `not_found` property of response.

    Parameters
    ----------
    prefix : str
        Icon set prefix.
    names : str, optional
        Icon name(s).
    """
    req = requests.get(f"{ROOT}/{prefix}.json?icons={','.join(names)}")
    req.raise_for_status()
    if (content := req.json()) == 404:
        raise requests.HTTPError(f"No data returned for {prefix!r}", response=req)
    return content  # type: ignore


def search(
    query: str,
    limit: int | None = None,
    start: int | None = None,
    prefixes: Sequence[str] | None = None,
    category: str | None = None,
    # similar: bool | None = None,
) -> APIv2SearchResponse:
    """Search icons.

    Example:
    https://api.iconify.design/search?query=arrows-horizontal&limit=999

    The Search query can include special keywords.

    For most keywords, the keyword and value can be separated by ":" or "=". It is
    recommended to use "=" because the colon can also be treated as icon set prefix.

    Keywords with boolean values can have the following values:

    "true" or "1" = true. "false" or "0" = false. Supported keywords:

    - `palette` (bool). Filter icon sets by palette.
      Example queries: "home palette=false", "cat palette=true".
    - `style` ("fill" | "stroke"). Filter icons by code.
      Example queries: "home style=fill", "cat style=stroke".
    - `fill` and `stroke` (bool). Same as above, but as boolean. Only one of keywords
      can be set: "home fill=true".
    - `prefix` (str). Same as prefix property from search query parameters, but in
      keyword. Overrides parameter.
    - `prefixes` (string). Same as prefixes property from
      search query parameters, but in keyword. Overrides parameter.

    Parameters
    ----------
    query : str
        Search string. Case insensitive.
    limit : int, optional
        Maximum number of items in response, default is 64. Min 32, max 999.
        If numer of icons in result matches limit, it means there are more icons to
        show.
    start : int, optional
        Start index for results, default is 0.
    prefixes : str, optional
        List of icon set prefixes. You can use partial prefixes that
        end with "-", such as "mdi-" matches "mdi-light".
    category : str, optional
        Filter icon sets by category.
    """
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if start is not None:
        params["start"] = start
    if prefixes is not None:
        if isinstance(prefixes, str):
            params["prefix"] = prefixes
        else:
            params["prefixes"] = ",".join(prefixes)
    if category is not None:
        params["category"] = category
    req = requests.get(f"{ROOT}/search?query={query}", params=params)
    req.raise_for_status()
    return req.json()  # type: ignore


def keywords(
    prefix: str | None = None, keyword: str | None = None
) -> APIv3KeywordsResponse:
    """Intended for use in suggesting search queries.

    One of prefix or keyword MUST be specified.

    Keyword can only contain letters numbers and dash.
    If it contains "-", only the last part after "-" is used.
    Must be at least 2 characters long.

    Parameters
    ----------
    prefix : str, optional
        Keyword Prefix.  API returns all keywords that start with `prefix`.
    keyword : str, optional
        Partial keyword. API returns all keywords that start or
        end with `keyword`.  (Ignored if `prefix` is specified).
    """
    if prefix:
        if keyword:
            warn("Both prefix and keyword specified. Ignoring keyword.")
        params = {"prefix": prefix}
    elif keyword:
        params = {"keyword": keyword}
    else:
        params = {}
    req = requests.get(f"{ROOT}/keywords", params=params)
    req.raise_for_status()
    return req.json()  # type: ignore


@lru_cache(maxsize=None)
def iconify_version() -> str:
    """Return version of iconify API."""
    req = requests.get(f"{ROOT}/version")
    req.raise_for_status()
    return req.text
