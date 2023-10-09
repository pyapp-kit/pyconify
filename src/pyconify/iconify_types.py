"""Type definitions for iconify response objects.

This module should only be imported behind a TYPE_CHECKING guard.
"""

from __future__ import annotations  # pragma: no cover

from typing import TYPE_CHECKING  # pragma: no cover

if TYPE_CHECKING:
    from typing import Literal, NotRequired, Required, TypedDict

    Rotation = Literal["90", "180", "270", 90, 180, 270, "-90", 1, 2, 3]
    Flip = Literal["horizontal", "vertical", "horizontal,vertical"]

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

        lastModified: dict[str, int]

    class IconifyOptional(TypedDict, total=False):
        """Optional properties that contain icon dimensions and transformations."""

        left: int  # left position of the ViewBox, default = 0
        top: int  # top position of the ViewBox, default = 0
        width: int  # width of the ViewBox, default = 16
        height: int  # height of the ViewBox, default = 16
        rotate: int  # number of 90-degree rotations (1=90deg, etc...), default = 0
        hFlip: bool  # horizontal flip, default = false
        vFlip: bool  # vertical flip, default = false

    class IconifyIcon(IconifyOptional, total=False):
        """Iconify icon object."""

        body: Required[str]

    class IconifyJSON(IconifyOptional, total=False):
        """Return value of icon_data(prefix, *names)."""

        prefix: Required[str]
        icons: Required[dict[str, IconifyIcon]]
        lastModified: int
        aliases: dict[str, str]
        not_found: list[str]

    class APIv2SearchResponse(TypedDict, total=False):
        """Return value of search(query)."""

        icons: list[str]  # list of prefix:name
        total: int  # Number of results. If same as `limit`, more results are available
        limit: int  # Number of results shown
        start: int  # Index of first result
        collections: dict[str, IconifyInfo]  # List of icon sets that match query
        request: APIv2SearchParams  # Copy of request parameters

    class APIv2SearchParams(TypedDict, total=False):
        """Request parameters for search(query)."""

        query: Required[str]  # search string
        limit: int  # maximum number of items in response
        start: int  # start index for results
        prefix: str  # filter icon sets by one prefix
        # collection: str  # filter icon sets by one collection
        prefixes: str  # filter icon sets by multiple prefixes or partial
        category: str  # filter icon sets by category
        similar: bool  # include partial matches for words  (default = True)

    class APIv3KeywordsResponse(TypedDict, total=False):
        """Return value of keywords()."""

        keyword: str  # one of these two will be there
        prefix: str
        exists: Required[bool]
        matches: Required[list[str]]
        invalid: Literal[True]
