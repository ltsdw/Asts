from asts.custom_typing.globals import GTK_VERSION, GOBJECT_VERSION

from gi import require_version
require_version(*GTK_VERSION)
require_version(*GOBJECT_VERSION)
from gi.repository.Gtk import TextBuffer
from gi.repository.GObject import Binding

from typing import Any

from asts.custom_typing.aliases import GObjectObjectHandlerID
from asts.custom_typing.base_gobject_object_wrapper import BaseGObjectObjectWrapper


class TextBufferWrapper(TextBuffer, BaseGObjectObjectWrapper):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Wrapper class around Gtk.TextBuffer to keep track of Gtk.TextBuffer bindings and handlers id.

        :param args: Positional arguments for Gtk.TextBuffer.
        :param kwargs: Keyword arguments for Gtk.TextBuffer.
        :return:
        """

        bindings: dict[str, Binding] = kwargs.pop("bindings", {})
        gobject_object_handlers_id: dict[str, GObjectObjectHandlerID] = kwargs.pop("gobject_object_handlers_id", {})

        TextBuffer.__init__(self, *args, **kwargs)
        BaseGObjectObjectWrapper.__init__(self, self, bindings, gobject_object_handlers_id)


__all__: list[str] = ["TextBufferWrapper"]

