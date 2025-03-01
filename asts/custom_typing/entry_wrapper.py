from asts.custom_typing.globals import GTK_VERSION, GOBJECT_VERSION

from gi import require_version
require_version(*GTK_VERSION)
require_version(*GOBJECT_VERSION)
from gi.repository.Gtk import Entry
from gi.repository.GObject import Binding

from typing import Any

from asts.custom_typing.base_widget_binding_wrapper import BaseWidgetBindingWrapper


class EntryWrapper(Entry, BaseWidgetBindingWrapper):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Wrapper class around Gtk.Entry to keep track of Gtk.Entry bindings.

        :param args: Positional arguments for Gtk.Entry.
        :param kwargs: Keyword arguments for Gtk.Entry.
        :return:
        """

        binding: Binding | None = kwargs.pop("binding", None)

        Entry.__init__(self, *args, **kwargs)
        BaseWidgetBindingWrapper.__init__(self, binding)


__all__: list[str] = ["EntryWrapper"]

