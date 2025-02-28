from asts.custom_typing.globals import GTK_VERSION

from gi import require_version
require_version(*GTK_VERSION)
from gi.repository.Gtk import TextIter


# Some type aliases
Command                 = str
Filename                = str
Filepath                = str
OptionalFilename        = str | None
OptionalFilepath        = OptionalFilename
OptionalAudioFilepath   = OptionalFilename
OptionalImageFilepath   = OptionalFilename
OptionalVideoFilepath   = OptionalFilename
SelectionBounds         = tuple[TextIter, TextIter] | tuple[()]
Timestamp               = str
OptionalTimestamp       = Timestamp | None
SourceID                = int


__all__: list[str] = [
    "Command", "Filename", "Filepath", "OptionalFilename", "OptionalFilepath",
    "OptionalAudioFilepath", "OptionalImageFilepath", "OptionalVideoFilepath",
    "SelectionBounds", "SourceID", "Timestamp", "OptionalTimestamp"
]

