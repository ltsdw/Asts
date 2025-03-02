from asts.custom_typing.globals import GOBJECT_VERSION, GLIB_VERSION

from gi import require_version
require_version(*GOBJECT_VERSION)
require_version(*GLIB_VERSION)
from gi.repository.GObject import Object, Property
from gi.repository.GLib import source_remove
from enum import Enum
from typing import Literal, overload

from asts.custom_typing.timestamp import Timestamp
from asts.custom_typing.aliases import GlibSourceID, StrTimestamp


class TimestampFieldInfoIndex(Enum):
    """
    TimestampFieldInfoIndex

    Simple Enum class to safely index TimestampFieldInfo.
    """

    TIMESTAMP       = 0
    GLIB_SOURCE_ID  = 1


    def __index__(self) -> Literal[0, 1]:
        return self.value


class TimestampFieldInfo(Object):
    def __init__(
        self,
        timestamp: Timestamp | StrTimestamp = Timestamp(),
        glib_source_id: GlibSourceID = 0
    ) -> None:
        """
        TimestampFieldInfo

        Class to hold information about for the timestamp fields and Glib.Source.glib_source_id
        (https://lazka.github.io/pgi-docs/#GLib-2.0/classes/Source.html#GLib.Source).

        The glib_source_id is mainly used to keep track of the glib_source_id of Glib.Source added by timeout_add,
        the timeout_add is used to tell wether or not the timestamp field is being edited.

        :param timestamp: (Optional) timestamp in the format HH:MM:SS.sss, ex 00:03:23.482.
        :param glib_source_id: (Optional) GLib.Source.glib_source_id.
        :return:
        """

        super().__init__()

        self._timestamp: Timestamp = timestamp if isinstance(timestamp, Timestamp) else Timestamp(timestamp)
        self._glib_source_id: GlibSourceID = glib_source_id


    @Property(type=StrTimestamp, default=Timestamp._DEFAULT_TIMESTAMP)
    def timestamp(self) -> StrTimestamp:
        return self._timestamp.timestamp


    @timestamp.setter
    def timestamp(self, value: Timestamp | StrTimestamp) -> None:
        if isinstance(value, Timestamp):
            if value == self._timestamp: return

            self._timestamp = value

            self.notify("timestamp")

            return

        if value == self._timestamp.timestamp: return

        self.notify("timestamp")

        self._timestamp.timestamp = value


    @Property(type=GlibSourceID, default=0)
    def glib_source_id(self) -> GlibSourceID:
        """
        glib_source_id

        :return: GLib.Source.glib_source_id.
        """

        return self._glib_source_id


    @glib_source_id.setter
    def glib_source_id(self, value: GlibSourceID) -> None:
        """
        glib_source_id

        :param value: GLib.Source.glib_source_id.
        :return:
        """

        self._glib_source_id = value


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
            TimestampFieldInfoIndex.GLIB_SOURCE_ID,
        ]
    ) -> GlibSourceID: ...


    def __getitem__(self, key: TimestampFieldInfoIndex) -> StrTimestamp | GlibSourceID:
        match key:
            case TimestampFieldInfoIndex.TIMESTAMP:
                return self.timestamp
            case TimestampFieldInfoIndex.GLIB_SOURCE_ID:
                return self.glib_source_id


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
            TimestampFieldInfoIndex.GLIB_SOURCE_ID
        ],
        value: GlibSourceID
    ) -> None: ...


    def __setitem__(self, key: TimestampFieldInfoIndex, value: Timestamp | StrTimestamp | GlibSourceID) -> None:
        match key:
            case TimestampFieldInfoIndex.TIMESTAMP:
                if not isinstance(value, Timestamp) and not isinstance(value, StrTimestamp):
                    raise TypeError(f"Expected Timestamp for {key}, but got {type(value)} instead.")

                self.timestamp = value
            case TimestampFieldInfoIndex.GLIB_SOURCE_ID:
                if not isinstance(value, GlibSourceID):
                    raise TypeError(f"Expected OptionalSourceID SourceID (int) for {key}, but got {type(value)} instead.")

                self.glib_source_id = value


    def set_property(self, property_name: str, value: object) -> None:
        """
        set_property

        Sets class's property if the specified type is valid.

        :param property_name: Name of the class's property that should be set.
        """

        if isinstance(value, Timestamp):
            self._timestamp.timestamp = value.timestamp

            self.notify("timestamp")

            return

        if isinstance(value, StrTimestamp):
            self._timestamp.timestamp = value

            self.notify("timestamp")

            return

        if isinstance(value, int):
            self._glib_source_id = value

            return

        raise TypeError(
            f"Could not convert {value} of type {type(value)} to the expected type {Timestamp | StrTimestamp} "
            f"when setting property {type(self)}.{property_name}."
        )


    def get_timestamp_object(self) -> Timestamp:
        """
        get_timestamp_object

        When the property getter isn't enough to assure timestamp correctness, use this instead.

        :return: The timestamp object hold by this class.
        """

        return self._timestamp


    def add_glib_source_id(self, glib_source_id: GlibSourceID) -> None:
        """
        add_glib_source_id

        Stores the GLib.Source.glib_source_id related to this GObject.Object.

        :param glib_source_id: GLib.Source.glib_source_id.
        :return:
        """

        self.remove_glib_source_id()
        self.glib_source_id = glib_source_id


    def remove_glib_source_id(self) -> None:
        """
        remove_glib_source_id

        Removes current stored GLib.Source.glib_source_id.

        :return:
        """

        if self._glib_source_id:
            source_remove(self._glib_source_id)

            self._glib_source_id = 0



__all__: list[str] = ["TimestampFieldInfo", "TimestampFieldInfoIndex"]

