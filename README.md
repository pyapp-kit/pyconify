# pyconify

[![License](https://img.shields.io/pypi/l/pyconify.svg?color=green)](https://github.com/pyapp-kit/pyconify/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/pyconify.svg?color=green)](https://pypi.org/project/pyconify)
[![Conda](https://img.shields.io/conda/vn/conda-forge/pyconify)](https://github.com/conda-forge/pyconify-feedstock)
[![Python Version](https://img.shields.io/pypi/pyversions/pyconify.svg?color=green)](https://python.org)
[![CI](https://github.com/pyapp-kit/pyconify/actions/workflows/ci.yml/badge.svg)](https://github.com/pyapp-kit/pyconify/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/pyapp-kit/pyconify/branch/main/graph/badge.svg)](https://codecov.io/gh/pyapp-kit/pyconify)

Python wrapper for the [Iconify](https://github.com/iconify) API.

Iconify is a versatile icon framework that includes 100+ icon sets with more
than 100,000 icons from FontAwesome, Material Design Icons, DashIcons, Feather
Icons, EmojiOne, Noto Emoji and many other open source icon sets.

Search for icons at: https://icon-sets.iconify.design

## Installation

```sh
pip install pyconify
# or
conda install -c conda-forge pyconify
```

## Usage

```python
import pyconify

# Info on available collections
collections = pyconify.collections()

# Info on specific collection(s)
details = pyconify.collection("fa", "fa-brands")

# Search for icons
hits = pyconify.search("python")

# Get icon data
data = pyconify.icon_data("fa-brands", "python")

# Get SVG
svg = pyconify.svg("fa-brands", "python")

# Get path to SVG on disk
# will either return cached version, or write to temp file
file_name = pyconify.svg_path("fa-brands", "python")

# Get CSS
css = pyconify.css("fa-brands", "python")

# Keywords
pyconify.keywords('home')

# API version
pyconify.iconify_version()
```

See details for each of these results in the [Iconify API documentation](https://iconify.design/docs/api/queries.html).

### cache

While the first fetch of any given SVG will require internet access,
pyconfiy caches svgs for faster retrieval and offline use. To
see or clear cache directory:

```python
import pyconify

# reveal location of cache
# will be ~/.cache/pyconify on linux and macos
# will be %LOCALAPPDATA%\pyconify on windows
# falls back to ~/.pyconify if none of the above are available
pyconify.get_cache_directory()

# remove the cache directory (and all its contents)
pyconify.clear_cache()
```

If you'd like to precache a number of svgs, the current recommendation
is to use the `svg()` function:

```python
import pyconify

ICONS_TO_STORE = {"mdi:bell", "mdi:bell-off", "mdi:bell-outline"}
for key in ICONS_TO_STORE:
    pyconify.svg(key)
```

Later calls to `svg()` will use the cached values.

To specify a custom cache directory, set the `PYCONIFY_CACHE` environment
variable to your desired directory.
To disable caching altogether, set the `PYCONIFY_CACHE` environment variable to
`false` or `0`.

### freedesktop themes

`pyconify` includes a convenience function to generate a directory of SVG files
in the [freedesktop icon theme specification](https://specifications.freedesktop.org/icon-theme-spec/icon-theme-spec-latest.html)

It takes a mapping of names from the [icon naming spec](https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html)
to iconify keys (e.g. `"prefix:icon"`). Icons will be placed in the
appropriate freedesktop subdirectory based on the icon name. Unknown icons will be placed
in the `other` subdirectory.

```python
from pyconify import freedesktop_theme
from pyconify.api import svg
icons = {
    "edit-copy": "ic:sharp-content-copy",
    "edit-delete": {"key": "ic:sharp-delete", "color": "red"},
    "weather-overcast": "ic:sharp-cloud",
    "weather-clear": "ic:sharp-wb-sunny",
    "bell": "bi:bell",
}
folder = freedesktop_theme(
    "mytheme",
    icons,
    base_directory="~/Desktop/icons",
)
```

would create

```
~/Desktop/icons/
├── mytheme
│   ├── actions
│   │   ├── edit-copy.svg
│   │   └── edit-delete.svg
│   ├── status
│   │   ├── weather-clear.svg
│   │   └── weather-overcast.svg
│   └── other
│       └── bell.svg
└── index.theme
```
