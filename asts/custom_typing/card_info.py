from enum import Enum
from typing import cast, Literal, overload, TypeVar

from asts.custom_typing.globals import REGEX_TIMESTAMP_PATTERN
from asts.custom_typing.aliases import (
    OptionalVideoFilepath, OptionalAudioFilepath, OptionalImageFilepath,
    OptionalTimestamp
)


_TypeCardInfoIndex = TypeVar("_TypeCardInfoIndex", bound="CardInfoIndex")

class CardInfoIndex(Enum):
    """
    DialogueInfoIndex

    Simple Enum class to safely index DialogueInfo data.
    """

    FRONT_FIELD         = 0
    BACK_FIELD          = 1
    START_TIMESTAMP     = 2
    END_TIMESTAMP       = 3
    VIDEO_FILEPATH      = 4
    AUDIO_FILEPATH      = 5
    IMAGE_FILEPATH      = 6
    OUT_OF_INDEX        = 7

    def __index__(self) -> Literal[0, 1, 2, 3, 4, 5, 6, 7]:
        return self.value


    def is_index(self: _TypeCardInfoIndex, index: _TypeCardInfoIndex) -> bool:
        return (self.value == index.value)


    def next(self: _TypeCardInfoIndex) -> _TypeCardInfoIndex:
        index: int = self.value + 1

        if index >= self.value: return self

        return cast(_TypeCardInfoIndex, CardInfoIndex(index))


_TypeCardInfo = TypeVar("_TypeCardInfo", bound="CardInfo")

class CardInfo:
    def __init__(
        self,
        front_field: str = "",
        back_field: str = "",
        start_timestamp: OptionalTimestamp = None,
        end_timestamp: OptionalTimestamp = None,
        video_filepath: OptionalVideoFilepath = None,
        audio_filepath: OptionalAudioFilepath = None,
        image_filepath: OptionalImageFilepath = None
    ) -> None:
        """
        CardInfo

        Simple class to hold information about a Anki card, its front and back field,
        aswell its media files.

        :param front_field: Front field of the card.
        :param back_backfield: Back field of the card.
        :param start_timestamp: Optional timestamp.
        :param end_timestamp: Optional timestamp.
        :param video_filepath: Optional filepath to a video to be added to the card.
        :param audio_filepath: Optional filepath to a audio to be added to the card.
        :param image_filepath: Optional filepath to a image to be added to the card.
        :return:
        """

        self._front_field: str = front_field
        self._back_field: str = back_field
        self._start_timestamp: OptionalTimestamp = None
        self._end_timestamp: OptionalTimestamp = None

        if start_timestamp and REGEX_TIMESTAMP_PATTERN.match(start_timestamp):
            self._start_timestamp = start_timestamp.replace(",",".")

        if end_timestamp and REGEX_TIMESTAMP_PATTERN.match(end_timestamp):
            self._end_timestamp = end_timestamp.replace(",",".")

        self._video_filepath: OptionalVideoFilepath = video_filepath
        self._audio_filepath: OptionalAudioFilepath = audio_filepath
        self._image_filepath: OptionalImageFilepath = image_filepath
        self._card_info_index: CardInfoIndex = CardInfoIndex.FRONT_FIELD


    def __iter__(self: _TypeCardInfo) -> _TypeCardInfo:
        return self


    def __next__(self) -> str | OptionalVideoFilepath | OptionalAudioFilepath | OptionalImageFilepath:
        if self._card_info_index.is_index(CardInfoIndex.OUT_OF_INDEX):
            raise StopIteration

        index: CardInfoIndex = self._card_info_index
        self._card_info_index = self._card_info_index.next()

        return self[index]


    @overload
    def __getitem__(
        self,
        key: Literal[
            CardInfoIndex.FRONT_FIELD,
            CardInfoIndex.BACK_FIELD
        ]
    ) -> str: ...


    @overload
    def __getitem__(
        self,
        key: Literal[
            CardInfoIndex.VIDEO_FILEPATH,
        ]
    ) -> OptionalVideoFilepath: ...


    @overload
    def __getitem__(
        self,
        key: Literal[
            CardInfoIndex.AUDIO_FILEPATH,
        ]
    ) -> OptionalAudioFilepath: ...


    @overload
    def __getitem__(
        self,
        key: Literal[
            CardInfoIndex.IMAGE_FILEPATH,
        ]
    ) -> OptionalImageFilepath: ...

    @overload
    def __getitem__(
        self,
        key: Literal[
            CardInfoIndex.START_TIMESTAMP,
            CardInfoIndex.END_TIMESTAMP
        ]) -> OptionalTimestamp: ...

    @overload
    def __getitem__(
        self,
        key: CardInfoIndex
    ) -> str | OptionalVideoFilepath | OptionalAudioFilepath | OptionalImageFilepath | OptionalTimestamp: ...


    def __getitem__(
        self,
        key: CardInfoIndex
    ) -> str | OptionalVideoFilepath | OptionalAudioFilepath | OptionalImageFilepath | OptionalTimestamp:
        match key:
            case CardInfoIndex.FRONT_FIELD:
                return self._front_field
            case CardInfoIndex.BACK_FIELD:
                return self._back_field
            case CardInfoIndex.START_TIMESTAMP:
                return self._start_timestamp
            case CardInfoIndex.END_TIMESTAMP:
                return self._end_timestamp
            case CardInfoIndex.VIDEO_FILEPATH:
                return self._video_filepath
            case CardInfoIndex.AUDIO_FILEPATH:
                return self._audio_filepath
            case CardInfoIndex.IMAGE_FILEPATH:
                return self._image_filepath


    @overload
    def __setitem__(
        self,
        key: Literal[
            CardInfoIndex.FRONT_FIELD,
            CardInfoIndex.BACK_FIELD
        ],
        value: str
    ) -> None: ...


    @overload
    def __setitem__(
        self,
        key: Literal[
            CardInfoIndex.VIDEO_FILEPATH,
        ],
        value: OptionalVideoFilepath
    ) -> None: ...


    @overload
    def __setitem__(
        self,
        key: Literal[
            CardInfoIndex.AUDIO_FILEPATH,
        ],
        value: OptionalAudioFilepath
    ) -> None: ...


    @overload
    def __setitem__(
        self,
        key: Literal[
            CardInfoIndex.IMAGE_FILEPATH,
        ],
        value: OptionalImageFilepath
    ) -> None: ...


    @overload
    def __setitem__(
        self,
        key: Literal[
            CardInfoIndex.START_TIMESTAMP,
            CardInfoIndex.END_TIMESTAMP
        ],
        value: OptionalTimestamp
    ) -> None: ...


    def __setitem__(self, key: CardInfoIndex, value: object) -> None:
        match key:
            case CardInfoIndex.FRONT_FIELD:
                if not isinstance(value, str):
                    raise TypeError(f"Expected {str} for {key}")

                self._front_field = value
            case CardInfoIndex.BACK_FIELD:
                if not isinstance(value, str):
                    raise TypeError(f"Expected {str} for {key}")

                self._back_field = value
            case CardInfoIndex.VIDEO_FILEPATH:
                if not isinstance(value, OptionalVideoFilepath):
                    raise TypeError(f"Expected {OptionalVideoFilepath} for {key}")

                self._video_filepath = value
            case CardInfoIndex.AUDIO_FILEPATH:
                if not isinstance(value, OptionalAudioFilepath):
                    raise TypeError(f"Expected {OptionalAudioFilepath} for {key}")

                self._audio_filepath = value
            case CardInfoIndex.IMAGE_FILEPATH:
                if not isinstance(value, OptionalImageFilepath):
                    raise TypeError(f"Expected {OptionalImageFilepath} for {key}")

                self._image_filepath = value
            case CardInfoIndex.START_TIMESTAMP:
                if not isinstance(value, OptionalTimestamp):
                    raise TypeError(f"Expected {OptionalTimestamp} for {key}")

                if value and REGEX_TIMESTAMP_PATTERN.match(value):
                    self._start_timestamp = value.replace(",",".")
            case CardInfoIndex.END_TIMESTAMP:
                if not isinstance(value, OptionalTimestamp):
                    raise TypeError(f"Expected {OptionalTimestamp} for {key}")

                if value and REGEX_TIMESTAMP_PATTERN.match(value):
                    self._end_timestamp = value.replace(",",".")


__all__: list[str] = ["CardInfo", "CardInfoIndex"]

