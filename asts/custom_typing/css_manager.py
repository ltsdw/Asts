from asts.custom_typing.globals import GTK_VERSION

from gi import require_version
require_version(*GTK_VERSION)
from gi.repository.Gtk import StyleContext
from gi.repository.Gtk import CssProvider

from re import compile, Pattern


class CssManager:
    # FIXME: Add more CSS support
    # right now this doesn't support rgb(100%, 100%, 100%, 100%) for example

    _REGEX_8BITS_HEX_COLOR: str = r"[0-9a-fA-F]{6,8}"
    _REGEX_16BITS_HEX_COLOR: str = r"[0-9a-fA-F]{12,16}"
    _REGEX_FLOATING_POINT: str = rf"\s*(?:0(?:\.\d+)?|1(?:\.0)?)\s*"
    _REGEX_8BITS_INTEGER: str = r"\s*(?:[01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])\s*"
    _REGEX_RGBA_8BITS_HEX: str = (
        rf"\s*#(?:{_REGEX_8BITS_HEX_COLOR})"
    )
    _REGEX_RGB_8BITS: str = (
        rf"(?:rgb\({_REGEX_8BITS_INTEGER},"
        rf"{_REGEX_8BITS_INTEGER},{_REGEX_8BITS_INTEGER}\))"
    )
    _REGEX_RGBA_8BITS: str = (
        rf"(?:rgba\({_REGEX_8BITS_INTEGER},{_REGEX_8BITS_INTEGER},"
        rf"{_REGEX_8BITS_INTEGER},{_REGEX_FLOATING_POINT}\))"
    )
    _REGEX_TEXT_PROPERTIES: str = (
        rf"(?:{_REGEX_RGBA_8BITS}|{_REGEX_RGB_8BITS}"
        rf"|{_REGEX_RGBA_8BITS_HEX})\s*;"
    )
    _REGEX_CSS_DECLARATION: Pattern[str] = compile(
        rf"(?:[a-zA-Z\-]+)\s*:\s*"
        rf"(?:{_REGEX_TEXT_PROPERTIES}|[a-zA-Z0-9]+\s*;|[\"\'][^\"\']+[\"\']\s*;)"
    )

    def __init__(self, style_context: StyleContext, priority: int) -> None:
        """
        CssManager

        Simple class that provides easy management of widget's context style and its css properties.

        :param style_context: Widget's StyleContext class object.
        :param priority: Priority which the css properties should be applied,
                         being STYLE_PROVIDER_PRIORITY_FALLBACK (1) the lowest
                         and STYLE_PROVIDER_PRIORITY_USER (800) the highest.
        :return:
        """

        self._css_string: str = ""
        self._css_data: dict[str, str] = {}
        self._css_provider: CssProvider = CssProvider()
        self._priority: int = priority
        self._style_context: StyleContext = style_context

        self._style_context.add_provider(self._css_provider, self._priority)


    def add_class(self, css_class_name: str, declaration: str) -> None:
        """
        add_class

        Creates a class name if it doesn't exist yet
        and add the declaration if it's well constructed.

        :param css_class_name: CSS's properties class name.
        :param declaration: CSS's declaration.
        :return:
        """

        matches: list[str] = [match for match in self._REGEX_CSS_DECLARATION.findall(declaration)]
        sanitized_declaration: str = "\n".join(matches)
        new_declaration: str = f"{{ {sanitized_declaration} }}"

        if not sanitized_declaration or self._css_data.get(css_class_name) == new_declaration: return

        self._css_data[css_class_name] = new_declaration

        self.reload_css()


    def __setitem__(self, key: str, value: str) -> None:
        """
        __setitem__

        Creates a class name if it doesn't exist yet
        and add the declaration if it's well constructed.

        Calls add_class internally.

        :param key: CSS's properties class name.
        :param value: CSS's declaration.
        :return:
        """

        self.add_class(key, value)


    def reload_css(self) -> None:
        """
        reload_css

        Reloads the CSS data and apply it to the CssProvider.
        If no change to the data was made whatsoever nothing is done.

        :return:
        """

        new_css_string = "\n".join(
            f"{class_name} {properties}"
            for class_name, properties
            in self._css_data.items()
        )

        if self._css_string == new_css_string: return

        self._css_string = new_css_string

        self._css_provider.load_from_string(self._css_string)


__all__: list[str] = ["CssManager"]

