from asts.custom_typing.globals import GTK_VERSION, GOBJECT_VERSION

from gi import require_version
require_version(*GTK_VERSION)
require_version(*GOBJECT_VERSION)
from gi.repository.GObject import Binding
from gi.repository.Gtk import CheckButton

from typing import Any

from asts.custom_typing.base_widget_binding_wrapper import BaseWidgetBindingWrapper


class CheckButtonWrapper(CheckButton, BaseWidgetBindingWrapper):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Wrapper class around Gtk.CheckButton to keep track of Gtk.CheckButton bindings.

        :param args: Positional arguments for Gtk.CheckButton.
        :param kwargs: Keyword arguments for Gtk.CheckButton.
        :return:
        """

        binding: Binding | None = kwargs.pop("binding", None)

        CheckButton.__init__(self, *args, **kwargs)
        BaseWidgetBindingWrapper.__init__(self, binding)


__all__: list[str] = ["CheckButtonWrapper"]

