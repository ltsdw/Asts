from enum import IntEnum


class FormatTags(IntEnum):
    """
    FormatTags

    Simple enum class to specify what type a tag should be formatted.

    HTML: Tags should be in html format.
    PANGO_MARKUP: Tags should be in pango markup format.
    """

    HTML = 0
    PANGO_MARKUP = 1


__all__: list[str] = ["FormatTags"]

