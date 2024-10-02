from asts.custom_typing.globals import GTK_VERSION

from gi import require_version
require_version(*GTK_VERSION)
from gi.repository.Gtk import TextBuffer, TextIter

from html.parser import HTMLParser
from re import compile, Match, Pattern


class TextBufferPangoMarkupParser(HTMLParser):
    # Urgh the ugliness of regex

    _SUPPORTED_FORMATTING_TAGS: list[str] = ["b", "i", "u"]
    _SUPPORTED_CONTAINER_TAGS: list[str] = ["span"]
    _SUPPORTED_TEXT_PROPERTIES: list[str] = ["foreground", "background"]
    _REGEX_8BITS_HEX_COLOR: str = r"[0-9a-fA-F]{6,8}"
    _REGEX_16BITS_HEX_COLOR: str = r"[0-9a-fA-F]{12,16}"
    _REGEX_PROPERTY_NAMES: str = (
        rf"\s*(?:{_SUPPORTED_TEXT_PROPERTIES[0]}|"
        rf"{_SUPPORTED_TEXT_PROPERTIES[1]})\s*=\s*"
    )
    _REGEX_RGB_8BITS_HEX: str = (
        rf"\s*#(?:{_REGEX_8BITS_HEX_COLOR})\s*"
    )
    _REGEX_RGBA_8BITS_HEX: str = (
        rf"\s*#(?:{_REGEX_8BITS_HEX_COLOR})\s*"
    )
    _REGEX_RGB_16BITS_HEX: str = (
        rf"\s*#(?:{_REGEX_16BITS_HEX_COLOR})\s*"
    )
    _REGEX_RGBA_16BITS_HEX: str = (
        rf"\s*#(?:{_REGEX_16BITS_HEX_COLOR})\s*"
    )
    _REGEX_TEXT_PROPERTIES: Pattern[str] = compile(
        rf"(?:{_REGEX_RGB_8BITS_HEX}|{_REGEX_RGBA_8BITS_HEX}|"
        rf"{_REGEX_RGB_16BITS_HEX}|{_REGEX_RGBA_16BITS_HEX})"
    )


    def __init__(self, text_buffer: TextBuffer) -> None:
        """
        TextBufferPangoMarkupParser

        A simple class to parse a html-like string and apply its tags and text to the text buffer.
        This class assumes that all tags are well formed
        and that the html fed is well structured.
        No sanitization is made internally,
        sanitization should be made to the string before feeding it to this class.

        :param text_buffer: The text buffer that should have the tags applied to.
        :return:
        """

        super().__init__()

        self._text_buffer: TextBuffer = text_buffer
        self._tags_stack: list[str] = []
        self._text_attributes_stack: list[tuple[str, str]] = []
        self._text: str = ""
        self._current_offset: int = 0


    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if not tag in self._SUPPORTED_FORMATTING_TAGS and tag not in self._SUPPORTED_CONTAINER_TAGS:
            return

        if tag in self._SUPPORTED_FORMATTING_TAGS:
            self._tags_stack.append(tag)
            return

        self._tags_stack.append(tag)

        for attr in attrs:
            if not attr[0] in self._SUPPORTED_TEXT_PROPERTIES:
                return

            if not attr[1]: continue

            attribute: Match[str] | None = self._REGEX_TEXT_PROPERTIES.match(attr[1])

            if not attribute: continue

            self._text_attributes_stack.append((attr[0], attribute.string.replace(" ", "")))


    def handle_endtag(self, tag: str):
        if not tag in self._SUPPORTED_FORMATTING_TAGS and tag not in self._SUPPORTED_CONTAINER_TAGS:
            return

        if tag in self._SUPPORTED_FORMATTING_TAGS:
            self._tags_stack.pop()
            return

        self._tags_stack.pop()
        self._text_attributes_stack = []


    def handle_data(self, data: str):
        len_data: int = len(data)
        start_iter: TextIter = self._text_buffer.get_iter_at_offset(self._current_offset)

        self._text_buffer.insert(start_iter, data)

        start_iter: TextIter = self._text_buffer.get_iter_at_offset(self._current_offset)
        end_iter: TextIter = self._text_buffer.get_iter_at_offset(self._current_offset + len_data)

        for tag in self._tags_stack:
            if not tag in self._SUPPORTED_FORMATTING_TAGS: continue

            self._text_buffer.apply_tag_by_name(tag, start_iter, end_iter)

        for (text_attribute, attribute_value) in self._text_attributes_stack:
            tag_name: str = f"{text_attribute}={attribute_value}"
            self._text_buffer.apply_tag_by_name(tag_name, start_iter, end_iter)

        self._text += data
        self._current_offset += len_data


    @property
    def text(self) -> str:
        return self._text


__all__: list[str] = ["TextBufferPangoMarkupParser"]

