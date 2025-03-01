from re import Match

from asts.custom_typing.globals import REGEX_TIMESTAMP_PATTERN
from asts.custom_typing.aliases import StrTimestamp


class Timestamp:
    _DEFAULT_TIMESTAMP: StrTimestamp = "00:00:00.000"

    def __init__(self, timestamp: "StrTimestamp | Timestamp" = _DEFAULT_TIMESTAMP) -> None:
        """
        A class to represent a timestamp in the format HH:MM:SS.sss.

        If internally the timestamp fails to be parsed the old value it was holding will be used,
        if the object is new and there is no privously timestamp the _DEFAULT_TIMESTAMP timestamp will be used.

        :param timestamp: A timestamp object or a string in the format HH:MM:SS.sss.
        "return"
        """

        self._timestamp: StrTimestamp

        if isinstance(timestamp, Timestamp):
            self._timestamp = timestamp.timestamp
        else:
            self._timestamp = self._parseTimestampInternal(timestamp)


    @property
    def timestamp(self) -> StrTimestamp:
        return self._timestamp


    @timestamp.setter
    def timestamp(self, value: StrTimestamp = _DEFAULT_TIMESTAMP) -> None:
        if value == self.timestamp: return

        self._timestamp = self._parseTimestampInternal(value)


    def _parseTimestampInternal(self, timestamp: StrTimestamp | None = None) -> StrTimestamp:
        """
        _parseTimestampInternal

        Try to parse the string as a timestamp in the format HH:MM:SS.sss.

        :param timestamp: Strin to be parsed.
        :return: The parsed timestamp or _DEFAULT_TIMESTAMP in case of fail.
        """

        result: StrTimestamp | None = self._parseTimestamp(timestamp) if timestamp else None

        if not result:
            return (self._timestamp if hasattr(self, "_timestamp") else self._DEFAULT_TIMESTAMP)

        return result


    @classmethod
    def _parseTimestamp(cls, timestamp: StrTimestamp) -> StrTimestamp | None:
        """
        _parseTimestamp

        Try to parse the string as a timestamp in the format HH:MM:SS.sss.

        :param timestamp: Strin to be parsed.
        :return: The parsed timestamp or None in case of fail.
        """

        result: Match[StrTimestamp] | None = REGEX_TIMESTAMP_PATTERN.match(timestamp) if timestamp else None

        if not result:
            return

        return result.group().replace(",", ".")


__all__: list[str] = ["Timestamp"]

