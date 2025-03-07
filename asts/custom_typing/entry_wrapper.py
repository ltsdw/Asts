from asts.custom_typing.globals import GTK_VERSION, GOBJECT_VERSION

from gi import require_version
require_version(*GTK_VERSION)
require_version(*GOBJECT_VERSION)
from gi.repository.Gtk import Entry
from gi.repository.GObject import Binding

from typing import Any

from asts.custom_typing.aliases import GObjectObjectHandlerID
from asts.custom_typing.base_gobject_object_wrapper import BaseGObjectObjectWrapper


class EntryWrapper(Entry, BaseGObjectObjectWrapper):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Wrapper class around Gtk.Entry to keep track of Gtk.Entry bindings.

        :param args: Positional arguments for Gtk.Entry.
        :param kwargs: Keyword arguments for Gtk.Entry.
        :return:
        """

        bindings: dict[str, Binding] = kwargs.pop("bindings", {})
        gobject_object_handlers_id: dict[str, GObjectObjectHandlerID] = kwargs.pop("gobject_object_handlers_id", {})

        Entry.__init__(self, *args, **kwargs)
        BaseGObjectObjectWrapper.__init__(self, self, bindings, gobject_object_handlers_id)


__all__: list[str] = ["EntryWrapper"]

