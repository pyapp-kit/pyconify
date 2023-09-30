# pyconify

[![License](https://img.shields.io/pypi/l/pyconify.svg?color=green)](https://github.com/pyapp-kit/pyconify/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/pyconify.svg?color=green)](https://pypi.org/project/pyconify)
[![Python Version](https://img.shields.io/pypi/pyversions/pyconify.svg?color=green)](https://python.org)
[![CI](https://github.com/pyapp-kit/pyconify/actions/workflows/ci.yml/badge.svg)](https://github.com/pyapp-kit/pyconify/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/pyapp-kit/pyconify/branch/main/graph/badge.svg)](https://codecov.io/gh/pyapp-kit/pyconify)

Python wrapper for the [Iconify](https://github.com/iconify) API.

Iconify is a versatile icon framework that includes 100+ icon sets with more
than 100,000 icons from FontAwesome, Material Design Icons, DashIcons, Feather
Icons, EmojiOne, Noto Emoji and many other open source icon sets.

Search for icons at: https://icon-sets.iconify.design

## Installation

```bash
pip install pyconify
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

# Get path to SVG temporary file for the session
file_name = pyconify.temp_svg("fa-brands", "python")

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
pyconfiy caches svgs for faster retrieval and offline use.  To
see or clear cache directory:

```python
import pyconify

pyconify.get_cache_directory()  # reveal location of cache
pyconify.clear_cache()  # remove the cache directory
```

If you'd like to precache a number of svgs, the current recommendation
is to use the `svg()` function:

```python
import pyconify

import pyconify

ICONS_TO_STORE = {"mdi:bell", "mdi:bell-off", "mdi:bell-outline"}
for key in ICONS_TO_STORE:
    pyconify.svg(key)
```

Later calls to `svg()` will use the cached values.
