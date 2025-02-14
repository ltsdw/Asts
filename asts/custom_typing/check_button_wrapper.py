from asts.custom_typing.globals import GTK_VERSION, GOBJECT_VERSION

from gi import require_version
require_version(*GTK_VERSION)
require_version(*GOBJECT_VERSION)
from gi.repository.Gtk import CheckButton
from gi.repository.GObject import Binding


class CheckButtonWrapper(CheckButton):
    def __init__(self, *args, **kwargs) -> None:
        """
        Wrapper class around Gtk.CheckButton to keep track of Gtk.CheckButton bindings.

        :param args: Positional arguments for Gtk.CheckButton.
        :param kwargs: Keyword arguments for Gtk.CheckButton.
        :return:
        """

        super().__init__(*args, **kwargs)

        self._binding: Binding | None = None


    @property
    def binding(self):
        return self._binding


    @binding.setter
    def binding(self, value: Binding) -> None:
        if self._binding == value: return

        self._binding = value


__all__: list[str] = ["CheckButtonWrapper"]

