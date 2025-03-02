from asts.custom_typing.globals import GOBJECT_VERSION

from gi import require_version
require_version(*GOBJECT_VERSION)
from gi.repository.GObject import Object, Binding

from asts.custom_typing.aliases import GObjectObjectHandlerID


class BaseGObjectObjectWrapper:
    def __init__(
        self,
        gobject_object: Object,
        bindings: dict[str, Binding] = {},
        gobject_object_handlers_id: dict[str, GObjectObjectHandlerID] = {}
    ) -> None:
        """
        Base wrapper class to keep track of GObject.Object's bindings.

        :param object: GObject.Object used.
        :param bindings: GObject.Object's binding list.
        :param gobject_object_handlers_id: GObject.Object's handlers' id.
        :return:
        """

        self._gobject_object: Object = gobject_object
        self._bindings: dict[str, Binding] = bindings
        self._gobject_object_handlers_id: dict[str, GObjectObjectHandlerID] = gobject_object_handlers_id


    def store_binding(self, source_property: str, binding: Binding) -> None:
        """
        store_binding

        Store this GObject.Object binding.

        :param source_property: Name of the property being binded.
        :param binding: Binding to be stored.
        :return:
        """

        maybe_binding: Binding | None = self._bindings.get(source_property)

        if maybe_binding: maybe_binding.unbind()

        self._bindings[source_property] = binding


    def remove_binding(self, source_property: str) -> None:
        """
        remove_binding

        Removes this specific GObject.Object's binding.

        After unbind the binding becomes invalid, you need to bind it again before calling this.

        :param source_property: Name of the property binded.
        :return:
        """

        bind: Binding | None = self._bindings.pop(source_property, None)

        if bind: bind.unbind()


    def remove_all_bindings(self) -> None:
        """
        remove_all_bindings

        Removes all bindings from this GObject.Object.

        After unbinding all bindings becomes invalid, you need to bind them again before calling this.

        :return:
        """

        keys: list[str] = list(self._bindings)

        for k in keys:
            self.remove_binding(k)


    def store_gobject_object_handler_id(self, detailed_signal: str, gobject_object_handler_id: GObjectObjectHandlerID) -> None:
        """
        store_gobject_object_handler_id

        Stores the GObject.Object handler id.

        :param detailed_signal: Name of the signal this GObject.Object connected to.
        :param gobject_object_handlers_id: GObject.Object's handler id.
        :return:
        """

        maybe_gobject_object_handler_id: GObjectObjectHandlerID | None = self._gobject_object_handlers_id.get(detailed_signal)

        if maybe_gobject_object_handler_id:
            self._gobject_object.disconnect(maybe_gobject_object_handler_id)

        self._gobject_object_handlers_id[detailed_signal] = gobject_object_handler_id


    def block_signal(self, detailed_signal: str) -> None:
        """
        block_signal

        Blocks the signal specified in detailed_signal if it's already stored.

        :param detailed_signal: Name of the signal this GObject.Object connected to.
        :return:
        """

        gobject_object_handler_id: GObjectObjectHandlerID | None = self._gobject_object_handlers_id.get(detailed_signal)

        if gobject_object_handler_id:
            self._gobject_object.handler_block(gobject_object_handler_id)


    def unblock_signal(self, detailed_signal: str) -> None:
        """
        unblock_signal

        Unblocks the signal specified in detailed_signal if it's already stored.

        :param detailed_signal: Name of the signal this GObject.Object connected to.
        :return:
        """

        gobject_object_handler_id: GObjectObjectHandlerID | None = self._gobject_object_handlers_id.get(detailed_signal)

        if gobject_object_handler_id: self._gobject_object.handler_unblock(gobject_object_handler_id)


    def block_all_signals(self) -> None:
        """
        block_all_signals

        Blocks all signals that are stored.

        :return:
        """

        for k in self._gobject_object_handlers_id.keys():
            self.block_signal(k)


    def unblock_all_signals(self) -> None:
        """
        unblock_all_signals

        Unblocks all signals that are stored.

        :return:
        """

        for k in self._gobject_object_handlers_id.keys():
            self.unblock_signal(k)


    def remove_signal(self, detailed_signal: str) -> None:
        """
        remove_signal

        Removes from signal handling for the signal specified by detailed_signal.

        :param detailed_signal: Name of the signal this GObject.Object connected to.
        :return:
        """

        gobject_object_handler_id: GObjectObjectHandlerID | None = self._gobject_object_handlers_id.pop(detailed_signal, None)

        if gobject_object_handler_id: self._gobject_object.disconnect(gobject_object_handler_id)


    def remove_all_signals(self) -> None:
        """
        remove_all_signal

        Removes all signals being handled handling.

        :return:
        """

        keys: list[str] = list(self._gobject_object_handlers_id)

        for k in keys:
            self.remove_signal(k)


    def block_interactions(self) -> None:
        """
        block_interactions

        Blocks any connected signal and unbind until unblock_interactions is called.

        Also removes all bindings, after calling bindings must be bind again.

        NOTE: I don't know if it's me and how I'm using these widgets in GTK4,
        but widgets recycling really messes up signals and logic behind it.

        :return:
        """

        self.remove_all_bindings()
        self.block_all_signals()


    def unblock_interactions(self) -> None:
        """
        Unblock_interactions

        Unblocks any blocked signal and bind its binding again if there's any.

        NOTE: I don't know if it's me and how I'm using these widgets in GTK4,
        but widgets recycling really messes up signals and logic behind it.

        :return:
        """

        self.unblock_all_signals()


__all__: list[str] = ["BaseGObjectObjectWrapper"]

