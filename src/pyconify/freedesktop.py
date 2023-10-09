from __future__ import annotations

import atexit
import shutil
from pathlib import Path
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Any, Mapping

from pyconify.api import svg

if TYPE_CHECKING:
    from typing_extensions import Required, TypedDict, Unpack

    from .iconify_types import Flip, Rotation

    class SVGKwargs(TypedDict, total=False):
        """Keyword arguments for the svg function."""

        color: str | None
        height: str | int | None
        width: str | int | None
        flip: Flip | None
        rotate: Rotation | None
        box: bool | None

    class SVGKwargsWithKey(SVGKwargs, total=False):
        """Keyword arguments for the svg function, with mandatory key."""

        key: Required[str]


MISC_DIR = "other"
HEADER = """
[Icon Theme]
Name={name}
Comment={comment}
Directories={directories}
"""
SUBDIR = """
[{directory}]
Size=16
MinSize=8
MaxSize=512
Type=Scalable
"""


def freedesktop_theme(
    name: str,
    icons: Mapping[str, str | SVGKwargsWithKey],
    comment: str = "pyconify-generated icon theme",
    base_directory: Path | str | None = None,
    **kwargs: Unpack[SVGKwargs],
) -> Path:
    """Create a freedesktop compliant theme folder.

    This function accepts a mapping of freedesktop icon name to iconify keys (or a dict
    of keyword arguments for the `pyconify.svg` function).  A new theme directory will
    be created in the `base_directory` with the given `name`.  The theme will contain
    a number of sub-directories, each containing the icons for that category.  An
    `index.theme` file will also be created in the theme directory.

    Categories are determined by the icon name, and are mapped to directories using the
    freedesktop [icon naming
    specification](https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html).
    For example, the if the key "edit-clear" appears in `icons`, the corresponding icon
    will be placed in the "actions" directory, whereas the key
    "accessories-calculator" would appear in the apps directory. Unrecognized keys
    will be placed in the "other" directory.  See the examples below for more details.

    Parameters
    ----------
    name : str
        The name of the theme.  A directory with this name will be created inside the
        `base_directory`.
    icons : Mapping[str, str | SVGKwargsWithKey]
        A mapping of freedesktop icon names to icon names or keyword arguments for
        the svg function. See note above and example below. Unrecognized keys are
        allowed, and will be placed in the "other" directory.
    comment : str, optional
        The comment for the index.theme, by default "pyconify-generated icon theme".
    base_directory : Path | str | None, optional
        The directory in which to create the theme. If `None`, a temporary directory
        will be created, and deleted when the program exits.  By default `None`.
    **kwargs : Unpack[SVGKwargs]
        Keyword arguments for the `pyconify.svg` function.  These will be passed to
        the svg function for each icon (unless overridden by the value in the `icons`
        mapping).

    Returns
    -------
    Path
        The path to the *base* directory of the theme. (NOT the path to the theme
        sub-directory which will have been created inside the base)

    Examples
    --------
    Pass a theme name and a mapping of freedesktop icon names to iconify keys or
    keyword arguments:

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

    This will create a folder structure as shown below.  Note that the `index.theme`
    file is also created, and files are placed in the appropriate freedesktop
    sub-directories. Unkown keys (like 'bell' in the example above) are placed in the
    "other" directory.

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

    Note that this folder may be used as a theme in Qt applications:

    ```python
    from qtpy.QtGui import QIcon
    from qtpy.QtWidgets import QApplication, QPushButton

    app = QApplication([])

    QIcon.setThemeSearchPaths([str(folder)])
    QIcon.setThemeName("mytheme")

    button = QPushButton()
    button.setIcon(QIcon.fromTheme("edit-clear"))
    button.show()

    app.exec()
    ```
    """
    if base_directory is None:
        base = Path(mkdtemp(prefix="pyconify-theme-icons"))

        @atexit.register
        def _cleanup() -> None:  # pragma: no cover
            shutil.rmtree(base, ignore_errors=True)

    else:
        base = Path(base_directory).expanduser().resolve()
        base.mkdir(parents=True, exist_ok=True)

    theme_dir = base / name
    theme_dir.mkdir(parents=True, exist_ok=True)

    dirs: set[str] = set()
    for file_name, _svg_kwargs in icons.items():
        # determine which directory to put the icon in
        file_key = file_name.lower().replace(".svg", "")
        subdir = FREEDESKTOP_ICON_TO_DIR.get(file_key, MISC_DIR)
        dest = theme_dir / subdir
        # create the directory if it doesn't exist
        dest.mkdir(parents=True, exist_ok=True)
        # add the directory to the list of directories
        dirs.add(subdir)

        # write the svg file
        if isinstance(_svg_kwargs, Mapping):
            _kwargs: Any = {**kwargs, **_svg_kwargs}
            if "key" not in _kwargs:
                raise ValueError("Expected 'key' in kwargs")  # pragma: no cover
            key = _kwargs.pop("key")  # must be present
        else:
            if not isinstance(_svg_kwargs, str):  # pragma: no cover
                raise TypeError(f"Expected icon name or dict, got {type(_svg_kwargs)}")
            key, _kwargs = _svg_kwargs, kwargs
        (dest / file_name).with_suffix(".svg").write_bytes(svg(key, **_kwargs))

    sorted_dirs = sorted(dirs)
    index = theme_dir / "index.theme"
    index_text = HEADER.format(
        name=name,
        comment=comment,
        directories=",".join(map(str.lower, sorted_dirs)),
    )
    for directory in sorted_dirs:
        index_text += SUBDIR.format(directory=directory.lower())
        if context := FREEDESKTOP_DIR_TO_CTX.get(directory):
            index_text += f"Context={context}\n"

    index.write_text(index_text)
    return base


# https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html

# mapping of directory name to Context
FREEDESKTOP_DIR_TO_CTX: dict[str, str] = {
    "actions": "Actions",
    "animations": "Animations",
    "apps": "Applications",
    "categories": "Categories",
    "devices": "Devices",
    "emblems": "Emblems",
    "emotes": "Emotes",
    "intl": "International",
    "mimetypes": "MimeTypes",
    "places": "Places",
    "status": "Status",
    MISC_DIR: "Other",
}

# mapping of directory name to icon names
FREEDESKTOP_DIR_ICONS: dict[str, set[str]] = {
    "actions": {
        "address-book-new",
        "application-exit",
        "appointment-new",
        "call-start",
        "call-stop",
        "contact-new",
        "document-new",
        "document-open",
        "document-open-recent",
        "document-page-setup",
        "document-print",
        "document-print-preview",
        "document-properties",
        "document-revert",
        "document-save",
        "document-save-as",
        "document-send",
        "edit-clear",
        "edit-copy",
        "edit-cut",
        "edit-delete",
        "edit-find",
        "edit-find-replace",
        "edit-paste",
        "edit-redo",
        "edit-select-all",
        "edit-undo",
        "folder-new",
        "format-indent-less",
        "format-indent-more",
        "format-justify-center",
        "format-justify-fill",
        "format-justify-left",
        "format-justify-right",
        "format-text-direction-ltr",
        "format-text-direction-rtl",
        "format-text-bold",
        "format-text-italic",
        "format-text-underline",
        "format-text-strikethrough",
        "go-bottom",
        "go-down",
        "go-first",
        "go-home",
        "go-jump",
        "go-last",
        "go-next",
        "go-previous",
        "go-top",
        "go-up",
        "help-about",
        "help-contents",
        "help-faq",
        "insert-image",
        "insert-link",
        "insert-object",
        "insert-text",
        "list-add",
        "list-remove",
        "mail-forward",
        "mail-mark-important",
        "mail-mark-junk",
        "mail-mark-notjunk",
        "mail-mark-read",
        "mail-mark-unread",
        "mail-message-new",
        "mail-reply-all",
        "mail-reply-sender",
        "mail-send",
        "mail-send-receive",
        "media-eject",
        "media-playback-pause",
        "media-playback-start",
        "media-playback-stop",
        "media-record",
        "media-seek-backward",
        "media-seek-forward",
        "media-skip-backward",
        "media-skip-forward",
        "object-flip-horizontal",
        "object-flip-vertical",
        "object-rotate-left",
        "object-rotate-right",
        "process-stop",
        "system-lock-screen",
        "system-log-out",
        "system-run",
        "system-search",
        "system-reboot",
        "system-shutdown",
        "tools-check-spelling",
        "view-fullscreen",
        "view-refresh",
        "view-restore",
        "view-sort-ascending",
        "view-sort-descending",
        "window-close",
        "window-new",
        "zoom-fit-best",
        "zoom-in",
        "zoom-original",
        "zoom-out",
    },
    "animations": {
        "process-working",
    },
    "apps": {
        "accessories-calculator",
        "accessories-character-map",
        "accessories-dictionary",
        "accessories-text-editor",
        "help-browser",
        "multimedia-volume-control",
        "preferences-desktop-accessibility",
        "preferences-desktop-font",
        "preferences-desktop-keyboard",
        "preferences-desktop-locale",
        "preferences-desktop-multimedia",
        "preferences-desktop-screensaver",
        "preferences-desktop-theme",
        "preferences-desktop-wallpaper",
        "system-file-manager",
        "system-software-install",
        "system-software-update",
        "utilities-system-monitor",
        "utilities-terminal",
    },
    "categories": {
        "applications-accessories",
        "applications-development",
        "applications-engineering",
        "applications-games",
        "applications-graphics",
        "applications-internet",
        "applications-multimedia",
        "applications-office",
        "applications-other",
        "applications-science",
        "applications-system",
        "applications-utilities",
        "preferences-desktop",
        "preferences-desktop-peripherals",
        "preferences-desktop-personal",
        "preferences-other",
        "preferences-system",
        "preferences-system-network",
        "system-help",
    },
    "devices": {
        "audio-card",
        "audio-input-microphone",
        "battery",
        "camera-photo",
        "camera-video",
        "camera-web",
        "computer",
        "drive-harddisk",
        "drive-optical",
        "drive-removable-media",
        "input-gaming",
        "input-keyboard",
        "input-mouse",
        "input-tablet",
        "media-flash",
        "media-floppy",
        "media-optical",
        "media-tape",
        "modem",
        "multimedia-player",
        "network-wired",
        "network-wireless",
        "pda",
        "phone",
        "printer",
        "scanner",
        "video-display",
    },
    "emblems": {
        "emblem-default",
        "emblem-documents",
        "emblem-downloads",
        "emblem-favorite",
        "emblem-important",
        "emblem-mail",
        "emblem-photos",
        "emblem-readonly",
        "emblem-shared",
        "emblem-symbolic-link",
        "emblem-synchronized",
        "emblem-system",
        "emblem-unreadable",
    },
    "emotes": {
        "face-angel",
        "face-angry",
        "face-cool",
        "face-crying",
        "face-devilish",
        "face-embarrassed",
        "face-kiss",
        "face-laugh",
        "face-monkey",
        "face-plain",
        "face-raspberry",
        "face-sad",
        "face-sick",
        "face-smile",
        "face-smile-big",
        "face-smirk",
        "face-surprise",
        "face-tired",
        "face-uncertain",
        "face-wink",
        "face-worried",
    },
    "mimetypes": {
        "application-x-executable",
        "audio-x-generic",
        "font-x-generic",
        "image-x-generic",
        "package-x-generic",
        "text-html",
        "text-x-generic",
        "text-x-generic-template",
        "text-x-script",
        "video-x-generic",
        "x-office-address-book",
        "x-office-calendar",
        "x-office-document",
        "x-office-presentation",
        "x-office-spreadsheet",
    },
    "places": {
        "folder",
        "folder-remote",
        "network-server",
        "network-workgroup",
        "start-here",
        "user-bookmarks",
        "user-desktop",
        "user-home",
        "user-trash",
    },
    "status": {
        "appointment-missed",
        "appointment-soon",
        "audio-volume-high",
        "audio-volume-low",
        "audio-volume-medium",
        "audio-volume-muted",
        "battery-caution",
        "battery-low",
        "dialog-error",
        "dialog-information",
        "dialog-password",
        "dialog-question",
        "dialog-warning",
        "folder-drag-accept",
        "folder-open",
        "folder-visiting",
        "image-loading",
        "image-missing",
        "mail-attachment",
        "mail-unread",
        "mail-read",
        "mail-replied",
        "mail-signed",
        "mail-signed-verified",
        "media-playlist-repeat",
        "media-playlist-shuffle",
        "network-error",
        "network-idle",
        "network-offline",
        "network-receive",
        "network-transmit",
        "network-transmit-receive",
        "printer-error",
        "printer-printing",
        "security-high",
        "security-medium",
        "security-low",
        "software-update-available",
        "software-update-urgent",
        "sync-error",
        "sync-synchronizing",
        "task-due",
        "task-past-due",
        "user-available",
        "user-away",
        "user-idle",
        "user-offline",
        "user-trash-full",
        "weather-clear",
        "weather-clear-night",
        "weather-few-clouds",
        "weather-few-clouds-night",
        "weather-fog",
        "weather-overcast",
        "weather-severe-alert",
        "weather-showers",
        "weather-showers-scattered",
        "weather-snow",
        "weather-storm",
    },
}

# reverse mapping of icon name to directory name
FREEDESKTOP_ICON_TO_DIR: dict[str, str] = {
    icn: dir_ for dir_, icons in FREEDESKTOP_DIR_ICONS.items() for icn in icons
}
