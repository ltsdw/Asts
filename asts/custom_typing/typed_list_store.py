from asts.custom_typing.globals import GIO_VERSION, GOBJECT_VERSION

from gi import require_version
require_version(*GIO_VERSION)
require_version(*GOBJECT_VERSION)
from gi.repository.Gio import ListStore
from gi.repository.GObject import Object

from typing import Iterator, cast, TypeVar, Generic


_T = TypeVar("_T", bound=Object)

class TypedListStore(Generic[_T]):
    def __init__(self, item_type: type[_T]) -> None:
        """
        TypedListStore

        A wrapper class around ListStore to leverage checking types to type checkers.

        :param item_type: The type the ListStore will hold.
        :return:
        """

        self._item_type: type[_T] = item_type
        self._liststore: ListStore = ListStore.new(item_type)


    def append(self, item: _T) -> None:
        self._liststore.append(item)


    def get_list_store(self) -> ListStore:
        """
        get_list_store

        Using this to edit the ListStore directly defeats the purpose of this class.
        This methods exists only because ListStore is expected by some functions
        and inheriting from ListStore adds too much complexity difficulting
        the usage of the generic type _T to override some functions.

        :return: The underlying ListStore.
        """

        return self._liststore


    def __getitem__(self, index: int) -> _T | None:
        item: Object | None = self._liststore.get_item(index)

        if item:
            return cast(_T, item)


    def __iter__(self) -> Iterator[_T]:
        return cast(Iterator[_T], self._liststore.__iter__())


    def __len__(self) -> int:
        return self._liststore.get_n_items()


__all__: list[str] = ["TypedListStore"]

