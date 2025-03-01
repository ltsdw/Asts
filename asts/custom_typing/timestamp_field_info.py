from asts.custom_typing.globals import GOBJECT_VERSION

from gi import require_version
require_version(*GOBJECT_VERSION)
from gi.repository.GObject import Object, Property

from enum import Enum
from typing import Literal, overload

from asts.custom_typing.timestamp import Timestamp
from asts.custom_typing.aliases import SourceID, StrTimestamp


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
    def __init__(
        self,
        timestamp: Timestamp | StrTimestamp = Timestamp(),
        source_id: SourceID = 0
    ) -> None:
        """
        TimestampFieldInfo

        Class to hold information about for the timestamp fields and Glib.Source.source_id
        (#https://lazka.github.io/pgi-docs/#GLib-2.0/classes/Source.html#GLib.Source).

        The source_id is mainly used to keep track of the source_id of Glib.Source added by timeout_add,
        the timeout_add is used to tell wether or not the timestamp field is being edited.

        :param timestamp: (Optional) timestamp in the format HH:MM:SS.sss, ex 00:03:23.482.
        :param source_id: (Optional) GLib.Source.source_id.
        :return:
        """

        super().__init__()

        self._timestamp: Timestamp = timestamp if isinstance(timestamp, Timestamp) else Timestamp(timestamp)
        self._source_id: SourceID = source_id


    @Property(type=StrTimestamp, default=Timestamp._DEFAULT_TIMESTAMP)
    def timestamp(self) -> StrTimestamp:
        return self._timestamp.timestamp


    @timestamp.setter
    def timestamp(self, value: Timestamp | StrTimestamp) -> None:
        if isinstance(value, Timestamp):
            if value == self._timestamp: return

            self._timestamp = value

            return

        if value == self._timestamp.timestamp: return

        self._timestamp.timestamp = value


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
    ) -> StrTimestamp: ...


    @overload
    def __getitem__(
        self,
        key: Literal[
            TimestampFieldInfoIndex.SOURCE_ID,
        ]
    ) -> SourceID: ...


    def __getitem__(self, key: TimestampFieldInfoIndex) -> StrTimestamp | SourceID:
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
        value: Timestamp | StrTimestamp
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
                if not isinstance(value, Timestamp) and not isinstance(value, StrTimestamp):
                    raise TypeError(f"Expected Timestamp for {key}, got {type(value)}.")

                self.timestamp = value
            case TimestampFieldInfoIndex.SOURCE_ID:
                if not isinstance(value, SourceID) or (value is None):
                    raise TypeError(f"Expected OptionalSourceID (int | None) for {key}, got {type(value)}.")

                self.source_id = value


    def set_property(self, property_name: str, value: object) -> None:
        """
        set_property

        Sets class's property if the specified type is valid.

        :param property_name: Name of the class's property that should be set.
        """

        if isinstance(value, Timestamp):
            self._timestamp.timestamp = value.timestamp

            return

        if isinstance(value, StrTimestamp):
            self._timestamp.timestamp = value

            return

        super().set_property(property_name, value)


    def getTimestampObject(self) -> Timestamp:
        """
        getTimestampObject

        When the property getter isn't enough to assure timestamp correctness, use this instead.

        :return: The timestamp object hold by this class.
        """

        return self._timestamp


__all__: list[str] = ["TimestampFieldInfo", "TimestampFieldInfoIndex"]

