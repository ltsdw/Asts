from asts.custom_typing.globals import GDK_VERSION

from gi import require_version
require_version(*GDK_VERSION)
from gi.repository.Gdk import RGBA as GdkRGBA

from typing import TypeVar

from asts.utils.core_utils import clamp


_TypeRGBA = TypeVar("_TypeRGBA", bound="RGBA")

class RGBA(GdkRGBA):
    def __init__(
        self,
        red: float = 0.0,
        green: float = 0.0,
        blue: float = 0.0,
        alpha: float = 1.0
    ) -> None:
        """
        RGBA

        Wrapper class around Gdk.RGBA to have a way to convert RGBA
        to hex color #rrrgggbbbaaa.

        :param red: Normalized red value.
        :param green: Normalized green value.
        :param blue: Normalized blue value.
        :return:
        """

        super().__init__()

        self.red: float = clamp(red, 0.0, 1.0)
        self.green: float = clamp(green, 0.0, 1.0)
        self.blue: float = clamp(blue, 0.0, 1.0)
        self.alpha: float = clamp(alpha, 0.0, 1.0)
        self._hash_str: str = str(self.hash())


    @property
    def hex_16bits_channel_string(self) -> str:
        """
        hex_16bits_channel_string

        Returns the rgba in hex #rrrrggggbbbbaaaa format, 16 bits per channel.

        :return: A string of the rgba color in hex #rrrrggggbbbbaaaa format.
        """

        red: int = int(0.5 + (self.red * 65535.0))
        green: int = int(0.5 + (self.green * 65535.0))
        blue: int = int(0.5 + (self.blue * 65535.0))
        alpha: int = int(self.alpha * 65535.0)

        return f"#{red:04X}{green:04X}{blue:04X}{alpha:04X}"


    @property
    def hex_8bits_channel_string(self) -> str:
        """
        hex_8bits_channel_string

        Returns the rgba in hex #rrggbbaa format, 8 bits per channel.

        :return: A string of the rgba color in hex #rrggbbaa format.
        """

        red: int = int(0.5 + (self.red * 255.0))
        green: int = int(0.5 + (self.green * 255.0))
        blue: int = int(0.5 + (self.blue * 255.0))
        alpha: int = int(0.5 +(self.alpha * 255.0))

        return f"#{red:02X}{green:02X}{blue:02X}{alpha:02X}"


    @classmethod
    def create_from(cls: type[_TypeRGBA], other_rgba: GdkRGBA) -> _TypeRGBA:
        """
        create_from

        Copies the properties from other_rgba to cls.

        :param other_rgba: Other Gdk.RGBA.
        :return: A new RGBA object.
        """

        return cls(other_rgba.red, other_rgba.green, other_rgba.blue, other_rgba.alpha)


    @property
    def hash_str(self) -> str:
        return self._hash_str


__all__: list[str] = ["RGBA"]

