from asts.custom_typing.globals import GOBJECT_VERSION

from gi import require_version
require_version(*GOBJECT_VERSION)
from gi.repository.GObject import Object, Property, ParamFlags

from enum import Enum
from typing import Literal, overload
from uuid import uuid1


class DialogueInfoIndex(Enum):
    """
    DialogueInfoIndex

    Simple Enum class to safely index DialogueInfo data.
    """

    DIALOGUE_INDEX  = 0
    DIALOGUE_UUID   = 1
    DIALOGUE        = 2
    START_TIMESTAMP = 3
    END_TIMESTAMP   = 4
    HAS_VIDEO       = 5
    HAS_AUDIO       = 6
    HAS_IMAGE       = 7


    def __index__(self) -> Literal[0, 1, 2, 3, 4, 5, 6, 7]:
        return self.value


class DialogueInfo(Object):
    __cls_index: int = 0

    def __init__(
        self,
        dialogue: str = "",
        start_time: str = "",
        end_time: str = "",
        has_video: bool = False,
        has_audio: bool = False,
        has_image: bool = False
    ) -> None:
        """
        DialogueInfo

        Class to hold information about a possible card, its index, dialogue, if it has audio, video, etc.
        Inherits from GObject.Object so it can then be used within Gio.ListStore.

        :param dialogue: Dialogue.
        :param start_time: Start time of the dialogue.
        :param end_time: End time of the dialogue.
        :param has_video: If the card has video media.
        :param has_audio: If the card has audio media.
        :param has_image: If the card has image media.
        :return:
        """

        super().__init__()

        self._index: int = DialogueInfo.__cls_index
        DialogueInfo.__cls_index += 1
        self._dialogue_uuid: str = str(uuid1())
        self._dialogue: str = dialogue
        self._start_time: str = start_time
        self._end_time: str = end_time
        self._has_video: bool = has_video
        self._has_audio: bool = has_audio
        self._has_image: bool = has_image


    @Property(type=str, default="", flags=ParamFlags.READABLE)
    def dialogue_uuid(self) -> str:
        return self._dialogue_uuid


    @Property(type=str, default="1", flags=ParamFlags.READABLE)
    def index(self) -> str:
        """
        index

        Index string GObject.Property.

        :return: One-based index as a string.
        """

        return str(self._index + 1)


    @Property(type=str, default="")
    def dialogue(self):
        return self._dialogue


    @dialogue.setter
    def dialogue(self, value: str) -> None:
        if self._dialogue == value: return

        self._dialogue = value

        self.notify("dialogue")


    @Property(type=str, default="")
    def start_time(self):
        return self._start_time


    @start_time.setter
    def start_time(self, value: str) -> None:
        if self._start_time == value: return

        self._start_time = value

        self.notify("start_time")


    @Property(type=str, default="")
    def end_time(self):
        return self._end_time


    @end_time.setter
    def end_time(self, value: str) -> None:
        if self._end_time == value: return

        self._end_time = value

        self.notify("end_time")


    @Property(type=bool, default=False)
    def has_video(self):
        return self._has_video


    @has_video.setter
    def has_video(self, value: bool) -> None:
        if self._has_video == value: return

        self._has_video = value

        self.notify("has_video")


    @Property(type=bool, default=False)
    def has_audio(self):
        return self._has_audio


    @has_audio.setter
    def has_audio(self, value: bool) -> None:
        if self._has_audio == value: return

        self._has_audio = value

        self.notify("has_audio")


    @Property(type=bool, default=False)
    def has_image(self):
        return self._has_image


    @has_image.setter
    def has_image(self, value: bool) -> None:
        if self._has_image == value: return

        self._has_image = value

        self.notify("has_image")


    @overload
    def __getitem__(
        self,
        key: Literal[
            DialogueInfoIndex.DIALOGUE_INDEX,
            DialogueInfoIndex.DIALOGUE_UUID,
            DialogueInfoIndex.DIALOGUE,
            DialogueInfoIndex.START_TIMESTAMP,
            DialogueInfoIndex.END_TIMESTAMP
        ]
    ) -> str: ...


    @overload
    def __getitem__(
        self,
        key: Literal[
            DialogueInfoIndex.HAS_VIDEO,
            DialogueInfoIndex.HAS_AUDIO,
            DialogueInfoIndex.HAS_IMAGE
        ]
    ) -> bool: ...


    def __getitem__(self, key: DialogueInfoIndex) -> str | bool:
        match key:
            case DialogueInfoIndex.DIALOGUE_UUID:
                return self.dialogue_uuid
            case DialogueInfoIndex.DIALOGUE_INDEX:
                return self.index
            case DialogueInfoIndex.DIALOGUE:
                return self.dialogue
            case DialogueInfoIndex.START_TIMESTAMP:
                return self.start_time
            case DialogueInfoIndex.END_TIMESTAMP:
                return self.end_time
            case DialogueInfoIndex.HAS_VIDEO:
                return self.has_video
            case DialogueInfoIndex.HAS_AUDIO:
                return self.has_audio
            case DialogueInfoIndex.HAS_IMAGE:
                return self.has_image


    @overload
    def __setitem__(
        self,
        key: Literal[
            DialogueInfoIndex.DIALOGUE_INDEX,
            DialogueInfoIndex.DIALOGUE_UUID,
            DialogueInfoIndex.DIALOGUE,
            DialogueInfoIndex.START_TIMESTAMP,
            DialogueInfoIndex.END_TIMESTAMP
        ],
        value: str
    ) -> None: ...


    @overload
    def __setitem__(
        self,
        key: Literal[
            DialogueInfoIndex.HAS_VIDEO,
            DialogueInfoIndex.HAS_AUDIO,
            DialogueInfoIndex.HAS_IMAGE
        ],
        value: bool
    ) -> None: ...


    def __setitem__(self, key: DialogueInfoIndex, value: object) -> None:
        match key:
            case DialogueInfoIndex.DIALOGUE_UUID:
                raise TypeError(f"Dialogue uuid shouldn't be directly set.")
            case DialogueInfoIndex.DIALOGUE_INDEX:
                raise TypeError(f"Dialogue index shouldn't be directly set.")
            case DialogueInfoIndex.DIALOGUE:
                if not isinstance(value, str):
                    raise TypeError(f"Expected string for {key}")

                self.dialogue = value
            case DialogueInfoIndex.START_TIMESTAMP:
                if not isinstance(value, str):
                    raise TypeError(f"Expected string for {key}")

                self.start_time = value
            case DialogueInfoIndex.END_TIMESTAMP:
                if not isinstance(value, str):
                    raise TypeError(f"Expected string for {key}")

                self.end_time = value
            case DialogueInfoIndex.HAS_VIDEO:
                if not isinstance(value, bool):
                    raise TypeError(f"Expected bool for {key}")

                self.has_video = value
            case DialogueInfoIndex.HAS_AUDIO:
                if not isinstance(value, bool):
                    raise TypeError(f"Expected bool for {key}")

                self.has_audio = value
            case DialogueInfoIndex.HAS_IMAGE:
                if not isinstance(value, bool):
                    raise TypeError(f"Expected bool for {key}")

                self.has_image = value


    def get_index(self) -> int:
        """
        get_index

        Returns the zero-based index of the dialogue,
        different from the property "index" which returns an one-based string index.

        :return: The index of the dialogue.
        """

        return self._index


    @classmethod
    def reset(cls) -> None:
        """
        reset

        Resets the class to a state before the first object was ever created.

        :return:
        """

        cls.__cls_index = 0


__all__: list[str] = ["DialogueInfo", "DialogueInfoIndex"]

