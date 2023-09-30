"""Wrapper for api calls at https://api.iconify.design/."""
from __future__ import annotations

import atexit
import os
import tempfile
import warnings
from contextlib import suppress
from typing import TYPE_CHECKING, Iterable, Literal, cast, overload

import requests

from ._cache import cache_key, svg_cache

if TYPE_CHECKING:
    from typing import Callable, TypeVar

    F = TypeVar("F", bound=Callable)

    from .iconify_types import (
        APIv2CollectionResponse,
        APIv2SearchResponse,
        APIv3KeywordsResponse,
        APIv3LastModifiedResponse,
        IconifyInfo,
        IconifyJSON,
        Rotation,
    )

    def lru_cache(maxsize: int | None = None) -> Callable[[F], F]:
        """Dummy lru_cache decorator for type checking."""

else:
    from functools import lru_cache


ROOT = "https://api.iconify.design"


@lru_cache(maxsize=None)
def collections(*prefixes: str) -> dict[str, IconifyInfo]:
    """Return collections where key is icon set prefix, value is IconifyInfo object.

    https://iconify.design/docs/api/collections.html

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
    resp = requests.get(f"{ROOT}/collections", params=query_params)
    resp.raise_for_status()
    return resp.json()  # type: ignore


@lru_cache(maxsize=None)
def collection(
    prefix: str,
    info: bool = False,
    chars: bool = False,
) -> APIv2CollectionResponse:
    """Return a list of icons in an icon set.

    https://iconify.design/docs/api/collection.html

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
    resp = requests.get(f"{ROOT}/collection?prefix={prefix}", params=query_params)
    resp.raise_for_status()
    if (content := resp.json()) == 404:
        raise requests.HTTPError(f"Icon set {prefix!r} not found.", response=resp)
    return content  # type: ignore


@lru_cache(maxsize=None)
def last_modified(*prefixes: str) -> APIv3LastModifiedResponse:
    """Return last modified date for icon sets.

    https://iconify.design/docs/api/last-modified.html

    Parameters
    ----------
    prefixes : Sequence[str], optional
        Comma separated list of icon set prefixes. You can use partial prefixes that
        end with "-", such as "mdi-" matches "mdi-light".  If None, return all
        collections.
    """
    # https://api.iconify.design/last-modified?prefixes=mdi,mdi-light,tabler
    query_params = {"prefixes": ",".join(prefixes)}
    resp = requests.get(f"{ROOT}/last-modified", params=query_params)
    resp.raise_for_status()
    return resp.json()  # type: ignore


# this function uses a special cache inside the body of the function
def svg(
    *key: str,
    color: str | None = None,
    height: str | int | None = None,
    width: str | int | None = None,
    flip: Literal["horizontal", "vertical", "horizontal,vertical"] | None = None,
    rotate: Rotation | None = None,
    box: bool | None = None,
) -> bytes:
    """Generate SVG for icon.

    https://iconify.design/docs/api/svg.html

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
    # check cache
    _kwargs = locals()
    _kwargs.pop("key")
    _key = cache_key(key, _kwargs)
    cache = svg_cache()
    if _key in cache:
        return cache[_key]

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
    resp = requests.get(f"{ROOT}/{prefix}/{name}.svg", params=query_params)
    resp.raise_for_status()
    if resp.content == b"404":
        raise requests.HTTPError(f"Icon '{prefix}:{name}' not found.", response=resp)

    # cache response and return
    cache[_key] = resp.content
    return resp.content


@lru_cache(maxsize=None)
def temp_svg(
    *key: str,
    color: str | None = None,
    height: str | int | None = None,
    width: str | int | None = None,
    flip: Literal["horizontal", "vertical", "horizontal,vertical"] | None = None,
    rotate: Rotation | None = None,
    box: bool | None = None,
    prefix: str | None = None,
    dir: str | None = None,
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
        with suppress(FileNotFoundError):  # pragma: no cover
            os.remove(tmp_name)

    return tmp_name


@lru_cache(maxsize=None)
def css(
    *keys: str,
    selector: str | None = None,
    common: str | None = None,
    override: str | None = None,
    pseudo: bool | None = None,
    var: str | None = None,
    square: bool | None = None,
    color: str | None = None,
    mode: Literal["mask", "background"] | None = None,
    format: Literal["expanded", "compact", "compressed"] | None = None,
) -> str:
    """Return CSS for `icons` in `prefix`.

    https://iconify.design/docs/api/css.html

    Iconify API can dynamically generate CSS for icons, where icons are used as
    background or mask image.

    Example:
    https://api.iconify.design/mdi.css?icons=account-box,account-cash,account,home

    Parameters
    ----------
    keys : str
        Icon set prefix and name(s). May be passed as a single string in the format
        `"prefix:name"` or as multiple strings: `'prefix', 'name1', 'name2'`.
        To generate CSS for icons from multiple icon sets, send separate queries for
        each icon set.
    selector : str, optional
        CSS selector for icons. If not set, defaults to ".icon--{prefix}--{name}"
        Variable "{prefix}" is replaced with icon set prefix, "{name}" with icon name.
    common : str, optional
        Common selector for icons, defaults to ".icon--{prefix}". Set it to empty to
        disable common code. Variable "{prefix}" is replaced with icon set prefix.
    override : str, optional
        Selector that mixes `selector` and `common` to generate icon specific
        style that overrides common style. Default value is
        `".icon--{prefix}.icon--{prefix}--{name}"`.
    pseudo : bool, optional
         Set it to `True` if selector for icon is a pseudo-selector, such as
         ".icon--{prefix}--{name}::after".
    var : str, optional
        Name for variable to use for icon, defaults to `"svg"` for monotone icons,
        `None` for icons with palette. Set to null to disable.
    square : bool, optional
        Forces icons to have width of 1em.
    color : str, optional
        Sets color for monotone icons. Also renders icons as background images.
    mode : Literal["mask", "background"], optional
        Forces icon to render as mask image or background image. If not set, mode will
        be detected from icon content: icons that contain currentColor will be rendered
        as mask image, other icons as background image.
    format : Literal["expanded", "compact", "compressed"], optional
        Stylesheet formatting option. Matches options used in Sass. Supported values
        are "expanded", "compact" and "compressed".
    """
    prefix, icons = _split_prefix_name(keys, allow_many=True)
    params: dict = {}
    if selector is not None:
        params["selector"] = selector
    if common is not None:
        params["common"] = common
    if override is not None:
        params["override"] = override
    if pseudo:
        params["pseudo"] = 1
    if var is not None:
        params["var"] = var
    if square:
        params["square"] = 1
    if color is not None:
        params["color"] = color
    if mode is not None:
        params["mode"] = mode
    if format is not None:
        params["format"] = format

    resp = requests.get(f"{ROOT}/{prefix}.css?icons={','.join(icons)}", params=params)
    resp.raise_for_status()
    return resp.text


def icon_data(prefix: str, *names: str) -> IconifyJSON:
    """Return icon data for `names` in `prefix`.

    https://iconify.design/docs/api/icon-data.html

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
    resp = requests.get(f"{ROOT}/{prefix}.json?icons={','.join(names)}")
    resp.raise_for_status()
    if (content := resp.json()) == 404:
        raise requests.HTTPError(f"No data returned for {prefix!r}", response=resp)
    return content  # type: ignore


def search(
    query: str,
    limit: int | None = None,
    start: int | None = None,
    prefixes: Iterable[str] | None = None,
    category: str | None = None,
    # similar: bool | None = None,
) -> APIv2SearchResponse:
    """Search icons.

    https://iconify.design/docs/api/search.html

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
    prefixes : str | Iterable[str], optional
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
    resp = requests.get(f"{ROOT}/search?query={query}", params=params)
    resp.raise_for_status()
    return resp.json()  # type: ignore


def keywords(
    prefix: str | None = None, keyword: str | None = None
) -> APIv3KeywordsResponse:
    """Intended for use in suggesting search queries.

    https://iconify.design/docs/api/keywords.html

    One of `prefix` or `keyword` MUST be specified.

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
            warnings.warn(
                "Cannot specify both prefix and keyword. Ignoring keyword.",
                stacklevel=2,
            )
        params = {"prefix": prefix}
    elif keyword:
        params = {"keyword": keyword}
    else:
        params = {}
    resp = requests.get(f"{ROOT}/keywords", params=params)
    resp.raise_for_status()
    return resp.json()  # type: ignore


@lru_cache(maxsize=None)
def iconify_version() -> str:
    """Return version of iconify API.

    https://iconify.design/docs/api/version.html

    The purpose of this query is to be able to tell which server you are connected to,
    but without exposing actual location of server, which can help debug error.
    This is used in networks when many servers are running.

    Examples
    --------
    >>> iconify_version()
    'Iconify API version 3.0.0-beta.1'
    """
    resp = requests.get(f"{ROOT}/version")
    resp.raise_for_status()
    return resp.text


@overload
def _split_prefix_name(
    key: tuple[str, ...], allow_many: Literal[False] = ...
) -> tuple[str, str]:
    ...


@overload
def _split_prefix_name(
    key: tuple[str, ...], allow_many: Literal[True]
) -> tuple[str, tuple[str, ...]]:
    ...


def _split_prefix_name(
    key: tuple[str, ...], allow_many: bool = False
) -> tuple[str, str] | tuple[str, tuple[str, ...]]:
    """Convenience function to split prefix and name from key.

    Examples
    --------
    >>> _split_prefix_name(("mdi", "account"))
    ("mdi", "account")
    >>> _split_prefix_name(("mdi:account",))
    ("mdi", "account")
    """
    if not key:
        raise ValueError("icon key must be at least one string.")
    if len(key) == 1:
        if ":" in key[0]:
            return tuple(key[0].split(":", maxsplit=1))  # type: ignore
        else:
            raise ValueError(
                "Single-argument icon names must be in the format 'prefix:name'. "
                f"Got {key[0]!r}"
            )
    elif len(key) == 2:
        return cast("tuple[str, str]", key)
    elif not allow_many:
        raise ValueError("icon key must be either 1 or 2 arguments.")
    return key[0], key[1:]
