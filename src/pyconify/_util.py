from collections import defaultdict
from pathlib import Path


def update_type_hints():
    from pyconify import api

    collections = api.collections()
    all_icons: defaultdict[str, set[str]] = defaultdict(set)

    for prefix in list(collections)[:1]:
        icons = api.collection(prefix)
        for icon_list in icons.get("categories", {}).values():
            all_icons[prefix].update(icon_list)
        all_icons[prefix].update(icons.get("uncategorized", []))

    module = "from typing import Literal\n\n"

    keys = [
        f'"{prefix}:{name}"'
        for prefix, names in sorted(all_icons.items())
        for name in sorted(names)
    ]
    inner = ",\n    ".join(keys)
    module += f"IconName = Literal[\n    {inner}\n]\n"
    Path(__file__).parent.joinpath("_typing.py").write_text(module)


update_type_hints()
