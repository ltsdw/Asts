from asts.custom_typing.globals import GOBJECT_VERSION

from gi import require_version
require_version(*GOBJECT_VERSION)
from gi.repository.GObject import Binding


class BaseWidgetBindingWrapper:
    def __init__(self, binding: Binding | None = None) -> None:
        """
        Base wrapper class to keep track of widgets' bindings.

        :param binding: Widget binding.
        :return:
        """

        self._binding: Binding | None = binding


    @property
    def binding(self) -> Binding | None:
        return self._binding


    @binding.setter
    def binding(self, value: Binding) -> None:
        if self._binding == value: return

        self._binding = value


    def bind(self, binding: Binding) -> None:
        """
        bind

        Store this widget binding.

        :param binding: Binding to be stored.
        :return:
        """

        self.binding = binding


    def unbind(self) -> None:
        """
        unbind

        Unbind any binding from this widget.

        :return:
        """

        if self._binding: self._binding.unbind()


__all__: list[str] = ["BaseWidgetBindingWrapper"]

