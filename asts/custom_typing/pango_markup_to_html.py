from asts.custom_typing.rgba import RGBA
from re import sub, search, Pattern, Match, compile, IGNORECASE


class PangoMarkupToHTML:
    _SUPPORTED_CONTAINER_TAGS: list[str] = ["span"]
    _SUPPORTED_TEXT_PROPERTIES: list[str] = ["foreground", "background"]
    _SUPPORTED_STYLE_ATTRIBUTE: list[str] = ["style"]
    _REGEX_SPAN_PATTERN: Pattern[str] = compile(
        rf"<{_SUPPORTED_CONTAINER_TAGS[0]}\s*([^>]*)\s*>",
        IGNORECASE
    )
    _REGEX_8BITS_HEX_COLOR: str = "[0-9a-fA-F]{6,8}"
    _REGEX_16BITS_HEX_COLOR: str = "[0-9a-fA-F]{12,16}"
    _REGEX_FOREGROUND_HEX_COLOR_PATTERN: Pattern[str] = (compile(
        rf"{_SUPPORTED_TEXT_PROPERTIES[0]}\s*=\s*\"("
        rf"#{_REGEX_8BITS_HEX_COLOR}|"
        rf"#{_REGEX_16BITS_HEX_COLOR})\"",
        IGNORECASE
        )
    )
    _REGEX_BACKGROUND_HEX_COLOR_PATTERN: Pattern[str] = (compile(
        rf"{_SUPPORTED_TEXT_PROPERTIES[1]}\s*=\s*\"("
        rf"#{_REGEX_8BITS_HEX_COLOR}|"
        rf"#{_REGEX_16BITS_HEX_COLOR})\"",
        IGNORECASE
        )
    )


    def __init__(self) -> None:
        """
        PangoMarkupToHTML

        Simple class to parse text with limited pango markup into limited supported html.
        No validation is made about the correctness of the markup formatting,
        it assumes the tags are well formed and correct.

        :return:
        """


    def _replace_match(self, match: Match[str]) -> str:
        """
        _replace_match

        Replaces the match found for another pattern and return the new string.

        :param match: Match to be replaced
        :return: New string with the text replaced
        """

        rgba: RGBA = RGBA()
        style_properties: list[str] = []

        foreground_color_match: Match[str] | None = (
            search(self._REGEX_FOREGROUND_HEX_COLOR_PATTERN, match.group(1))
        )
        background_color_match: Match[str] | None = (
            search(self._REGEX_BACKGROUND_HEX_COLOR_PATTERN, match.group(1))
        )

        if foreground_color_match:
            rgba.parse(foreground_color_match.group(1))

            style_properties.append(f"color: {rgba.hex_8bits_channel_string};")

        if background_color_match:
            rgba.parse(background_color_match.group(1))

            style_properties.append(f"background-color: {rgba.hex_8bits_channel_string};")

        if not style_properties: return f"<{self._SUPPORTED_CONTAINER_TAGS}>"

        return (
            f"<{self._SUPPORTED_CONTAINER_TAGS[0]} {self._SUPPORTED_STYLE_ATTRIBUTE[0]}="
            f"\"{ ' '.join(style_properties) }\">"
        )


    def get_text_parsed(self, text: str) -> str:
        """
        get_text_parsed

        Parses the text into supported html tags.

        :param text: Text to with pango markup formatting to be parsed.
        :return: The text with its pango markup tags parsed into limited supported html.
        """

        return sub(self._REGEX_SPAN_PATTERN, self._replace_match, text)


__all__: list[str] = ["PangoMarkupToHTML"]

