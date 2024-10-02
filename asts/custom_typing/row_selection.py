class RowSelection:
    def __init__(self, index: int) -> None:
        """
        RowSelection

        A simple class to hold information about the row that is indexed.

        :param index: The last indexed row.
        :return:
        """

        self._has_selection_updates_blocked: bool = False
        self._selected_row_index: int = index


    @property
    def index(self) -> int:
        return self._selected_row_index


    @index.setter
    def index(self, index: int) -> None:
        self._selected_row_index = index


    @property
    def has_selection_updates_blocked(self) -> bool:
        return self._has_selection_updates_blocked


    def block_selection_updates(self) -> None:
        self._has_selection_updates_blocked = True


    def unblock_selection_updates(self) -> None:
        self._has_selection_updates_blocked = False


__all__: list[str] = ["RowSelection"]

