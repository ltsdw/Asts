from asts.custom_typing.globals import GOBJECT_VERSION

from gi import require_version
require_version(*GOBJECT_VERSION)
from gi.repository.GObject import Object, Property

from enum import Enum
from typing import Literal, overload
from re import Match

from asts.custom_typing.globals import REGEX_TIMESTAMP_PATTERN
from asts.custom_typing.aliases import OptionalTimestamp, Timestamp, SourceID


class TimestampFieldInfoIndex(Enum):
    """
    TimestampFieldInfoIndex

    Simple Enum class to safely index TimestampFieldInfo.
    """

    TIMESTAMP  = 0
    SOURCE_ID  = 1


    def __index__(self) -> Literal[0, 1]:
        return self.value


class TimestampFieldInfo(Object):
    _DEFAULT_TIMESTAMP: Timestamp = "00:00:00.000"


    def __init__(
        self,
        timestamp: OptionalTimestamp = None,
        source_id: SourceID = 0
    ) -> None:
        """
        TimestampFieldInfo

        Class to hold information about for the timestamp fields and Glib.Source.source_id
        (#https://lazka.github.io/pgi-docs/#GLib-2.0/classes/Source.html#GLib.Source).

        The source_id is mainly used to keep track of the source_id of Glib.Source added by timeout_add,
        the timeout_add is used to tell wether or not the timestamp field is being edited.

        :param timestamp: (Optional) timestamp in the format HH:MM:SS.SSS, ex 00:03:23.482.
        :param source_id: (Optional) GLib.Source.source_id.
        :return:
        """

        super().__init__()

        self._timestamp: Timestamp = self._parseTimestamp(timestamp)
        self._source_id: SourceID = source_id


    @Property(type=str, default=_DEFAULT_TIMESTAMP)
    def timestamp(self) -> Timestamp:
        return self._timestamp


    @timestamp.setter
    def timestamp(self, value: OptionalTimestamp) -> None:
        if value == self.timestamp: return

        self._timestamp = self._parseTimestamp(value)


    @Property(type=SourceID, default=0)
    def source_id(self) -> SourceID:
        """
        source_id

        :return: GLib.Source.source_id.
        """

        return self._source_id


    @source_id.setter
    def source_id(self, value: SourceID) -> None:
        """
        source_id

        :param value: GLib.Source.source_id.
        :return:
        """

        self._source_id = value


    @overload
    def __getitem__(
        self,
        key: Literal[
            TimestampFieldInfoIndex.TIMESTAMP,
        ]
    ) -> Timestamp: ...


    @overload
    def __getitem__(
        self,
        key: Literal[
            TimestampFieldInfoIndex.SOURCE_ID,
        ]
    ) -> SourceID: ...


    def __getitem__(self, key: TimestampFieldInfoIndex) -> Timestamp | SourceID:
        match key:
            case TimestampFieldInfoIndex.TIMESTAMP:
                return self.timestamp
            case TimestampFieldInfoIndex.SOURCE_ID:
                return self.source_id


    @overload
    def __setitem__(
        self,
        key: Literal[
            TimestampFieldInfoIndex.TIMESTAMP
        ],
        value: OptionalTimestamp
    ) -> None: ...


    @overload
    def __setitem__(
        self,
        key: Literal[
            TimestampFieldInfoIndex.SOURCE_ID
        ],
        value: SourceID
    ) -> None: ...


    def __setitem__(self, key: TimestampFieldInfoIndex, value: object) -> None:
        match key:
            case TimestampFieldInfoIndex.TIMESTAMP:
                if not isinstance(value, Timestamp) or (value is None):
                    raise TypeError(f"Expected OptionalTimestamp (str | None) for {key}.")

                self.timestamp = value
            case TimestampFieldInfoIndex.SOURCE_ID:
                if not isinstance(value, SourceID) or (value is None):
                    raise TypeError(f"Expected OptionalSourceID (int | None) for {key}.")

                self.source_id = value


    def _parseTimestamp(self, timestamp: OptionalTimestamp) -> Timestamp:
        """
        _parseTimestamp

        Try parsing the timestamp string.

        :param timestamp: (Optional) timestamp.
        :return: If the 'timestamp' parameter is valid, return it, otherwise return a _DEFAULT_TIMESTAMP.
        """

        result: Match[Timestamp] | None = REGEX_TIMESTAMP_PATTERN.match(timestamp) if timestamp else None

        if not result:
            return (self._timestamp if hasattr(self, "_timestamp") else self._DEFAULT_TIMESTAMP)

        return result.group().replace(",", ".")


    def __str__(self) -> Timestamp:
        return self.timestamp


__all__: list[str] = ["TimestampFieldInfo", "TimestampFieldInfoIndex"]

