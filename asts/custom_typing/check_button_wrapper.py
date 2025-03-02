from asts.custom_typing.globals import GTK_VERSION, GOBJECT_VERSION

from gi import require_version
require_version(*GTK_VERSION)
require_version(*GOBJECT_VERSION)
from gi.repository.GObject import Binding
from gi.repository.Gtk import CheckButton

from typing import Any

from asts.custom_typing.aliases import GObjectObjectHandlerID
from asts.custom_typing.base_gobject_object_wrapper import BaseGObjectObjectWrapper


class CheckButtonWrapper(CheckButton, BaseGObjectObjectWrapper):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Wrapper class around Gtk.CheckButton to keep track of Gtk.CheckButton bindings.

        :param args: Positional arguments for Gtk.CheckButton.
        :param kwargs: Keyword arguments for Gtk.CheckButton.
        :return:
        """

        bindings: dict[str, Binding] = kwargs.pop("bindings", {})
        gobject_object_handlers_id: dict[str, GObjectObjectHandlerID] = kwargs.pop("gobject_object_handlers_id", {})

        CheckButton.__init__(self, *args, **kwargs)
        BaseGObjectObjectWrapper.__init__(self, self, bindings, gobject_object_handlers_id)


__all__: list[str] = ["CheckButtonWrapper"]

