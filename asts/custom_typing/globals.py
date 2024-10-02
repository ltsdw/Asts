# Gtk versioning
GTK_VERSION:    tuple[str, str] = ("Gtk",       "4.0")
GDK_VERSION:    tuple[str, str] = ("Gdk",       "4.0")
PANGO_VERSION:  tuple[str, str] = ("Pango",     "1.0")
GIO_VERSION:    tuple[str, str] = ("Gio",       "2.0")
GOBJECT_VERSION:tuple[str, str] = ("GObject",   "2.0")
GLIB_VERSION:   tuple[str, str] = ("GLib",      "2.0")

from gi import require_version
require_version(*GTK_VERSION)
require_version(*GDK_VERSION)
from gi.repository.Gdk import Display, Monitor
from gi.repository.Gtk import init as _

from sys import argv
from os import path
from typing import cast, Callable, Pattern
from re import compile

from asts.utils.core_utils import die


# Default display
__display: Display | None = Display.get_default()
DISPLAY: Display = __display if __display else die("Failed to get the default display, exiting...")

# Loads the primary monitor width x height
__get_primary_monitor_width: Callable[[], int] = (
    lambda: cast(Monitor, DISPLAY.get_monitors()[0]).get_geometry().width
)
__get_primary_monitor_height: Callable[[], int] = (
    lambda: cast(Monitor, DISPLAY.get_monitors()[0]).get_geometry().height
)
DISPLAY_WIDTH: int = __get_primary_monitor_width()
DISPLAY_HEIGHT: int = __get_primary_monitor_height()

APPLICATION_ROOT_DIRECTORY: str = path.dirname(path.abspath(argv[0]))
CACHE_DIR: str = path.join(APPLICATION_ROOT_DIRECTORY, "cache")
CACHE_MEDIA_DIR: str = path.join(CACHE_DIR, "media")
RECENTLY_USED_FILEPATH: str = path.join(CACHE_DIR, "recently_used")
ICONS_SYMBOLIC_DIRECTORY: str = path.join(
    APPLICATION_ROOT_DIRECTORY,
    "icons",
    "hicolor",
    "symbolic",
    "apps"
)

# Supported media files format
VIDEO_FORMAT: str = ".mp4"
AUDIO_FORMAT: str = ".mp3"
IMAGE_FORMAT: str = ".bmp"

# Regex to match timestamp
REGEX_TIMESTAMP_PATTERN: Pattern[str] = compile(r"^(?:[0-9]{2,3}:[0-9]{2}:[0-9]{2}[.,][0-9]{3})$")

__all__: list[str] = [
    "GTK_VERSION", "GDK_VERSION", "GLIB_VERSION", "GIO_VERSION",
    "GOBJECT_VERSION", "PANGO_VERSION", "DISPLAY", "DISPLAY_WIDTH",
    "DISPLAY_HEIGHT", "APPLICATION_ROOT_DIRECTORY", "CACHE_DIR", "CACHE_MEDIA_DIR",
    "RECENTLY_USED_FILEPATH", "ICONS_SYMBOLIC_DIRECTORY", "REGEX_TIMESTAMP_PATTERN",
    "VIDEO_FORMAT", "AUDIO_FORMAT", "IMAGE_FORMAT"
]

