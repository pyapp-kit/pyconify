from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from logging import warn
from typing import TYPE_CHECKING, Literal, Sequence

import requests

if TYPE_CHECKING:
    from typing import NotRequired, Required, TypedDict

    class Author(TypedDict, total=False):
        """Author information."""

        name: Required[str]  # author name
        url: NotRequired[str]  # author website

    class License(TypedDict, total=False):
        """License information."""

        title: Required[str]  # license title
        spdx: str  # SPDX license ID
        url: str  # license URL

    class IconifyInfo(TypedDict, total=False):
        """Icon set information block."""

        name: Required[str]  # icon set name
        author: Required[Author]  # author info
        license: Required[License]  # license info
        total: int  # total number of icons
        version: str  # version string
        height: int | list[int]  # Icon grid: number or array of numbers.
        displayHeight: int  # display height for samples: 16 - 24
        category: str  # category on Iconify collections list
        tags: list[str]  # list of tags to group similar icon sets
        # True if icons have predefined color scheme, false if icons use currentColor.
        palette: bool  # palette status.
        hidden: bool  # if true, icon set should not appear in icon sets list

    class APIv2CollectionResponse(TypedDict, total=False):
        """Object returned from collection(prefix)."""

        prefix: Required[str]  # icon set prefix
        total: Required[int]  # Number of icons (duplicate of info?.total)
        title: str  # Icon set title, if available (duplicate of info?.name)
        info: IconifyInfo  # Icon set info
        uncategorized: list[str]  # List of icons without categories
        categories: dict[str, list[str]]  # List of icons, sorted by category
        hidden: list[str]  # List of hidden icons
        aliases: dict[str, str]  # List of aliases, key = alias, value = parent icon
        chars: dict[str, str]  # Characters, key = character, value = icon name
        # https://iconify.design/docs/types/iconify-json-metadata.html#themes
        prefixes: dict[str, str]
        suffixes: dict[str, str]

    class APIv3LastModifiedResponse(TypedDict):
        """key is icon set prefix, value is lastModified property from that icon set."""

        lastModified: dict[str, datetime]

    class IconData(TypedDict, total=False):
        prefix: str
        lastModified: datetime
        aliases: dict[str, str]
        width: int
        height: int
        icons: dict[str, str]
        not_found: list[str]

    class APIv2SearchResponse(TypedDict, total=False):
        icons: list[str]  # list of prefix:name
        total: int  # Number of results. If same as `limit`, more results are available
        limit: int  # Number of results shown
        start: int  # Index of first result
        collections: dict[str, IconifyInfo]  # List of icon sets that match query
        request: APIv2SearchParams  # Copy of request parameters

    class APIv2SearchParams(TypedDict, total=False):
        query: Required[str]  # search string
        limit: int  # maximum number of items in response
        start: int  # start index for results
        prefix: str  # filter icon sets by one prefix
        # collection: str  # filter icon sets by one collection
        prefixes: str  # filter icon sets by multiple prefixes or partial
        category: str  # filter icon sets by category
        similar: bool  # include partial matches for words  (default = True)

    class APIv3KeywordsResponse(TypedDict, total=False):
        keyword: str  # one of these two will be there
        prefix: str
        exists: Required[bool]
        matches: Required[list[str]]
        invalid: Literal[True]


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
    data = req.json()
    if "lastModified" in data:
        data["lastModified"] = {
            k: datetime.utcfromtimestamp(v) for k, v in data["lastModified"].items()
        }
    return data  # type: ignore


@lru_cache(maxsize=None)
def svg(
    prefix: str,
    name: str,
    color: str | None = None,
    height: str | int | None = None,
    width: str | int | None = None,
    flip: Literal["horizontal", "vertical", "horizontal,vertical"] | None = None,
    rotate: str | int | None = None,
    box: bool = False,
) -> str:
    """Generate SVG for icon.

    Parameters
    ----------
    prefix : str
        Icon set prefix.
    name : str
        Icon name.
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
    # https://api.iconify.design/fluent-emoji-flat/alarm-clock.svg?height=48&width=48
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
    return req.text  # type: ignore


def icon_data(prefix: str, *names: str) -> IconData:
    """Return a dict of icon data where key is icon name and value is icon data.

    Parameters
    ----------
    prefix : str
        Icon set prefix.
    names : str, optional
        Icon name(s).
    """
    # https://api.iconify.design/mdi.json?icons=acount-box,account-cash,account,home

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
    # https://api.iconify.design/search?query=arrows-horizontal&limit=999
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


def keywords(prefix: str | None = None, keyword: str | None = None):
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


def version() -> str:
    """Return version of iconify API."""
    req = requests.get(f"{ROOT}/version")
    req.raise_for_status()
    return req.text
