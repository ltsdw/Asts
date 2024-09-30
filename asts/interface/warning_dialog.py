from asts.custom_typing.globals import GTK_VERSION, GIO_VERSION

from gi import require_version
require_version(*GTK_VERSION)
require_version(*GIO_VERSION)
from gi.repository.Gtk import (
    Align, Box, Button, Frame, Image,
    Label, Orientation, Window
)
from gi.repository.Gio import Icon

from os import path

from asts.custom_typing.aliases import Filepath
from asts.custom_typing.globals import DISPLAY_WIDTH, DISPLAY_HEIGHT, ICONS_SYMBOLIC_DIRECTORY
from asts.utils.extra_utils import set_widget_margin


class WarningDialog(Window):
    def __init__(
        self,
        parent: Window,
        warning_message: str = "Warning went wrong."
    ) -> None:
        """
        WarningDialog

        Window dialog to display a simple warning message.

        :param parent: The parent window where the button is placed.
        :param warning_warning_message: The text that should be displayed as a warning.
        :return:
        """

        super().__init__(
            title='Warning - Something went wrong',
            transient_for=parent,
            modal=True
        )

        self.set_default_size(int(DISPLAY_WIDTH * 0.35), int(DISPLAY_HEIGHT * 0.35))

        self._main_box: Box = Box(orientation=Orientation.VERTICAL)
        self._image_label_box: Box = Box(orientation=Orientation.VERTICAL)
        image_label_frame: Frame = Frame(child=self._image_label_box)
        frame: Frame = Frame(child=self._main_box)
        self._warning_message: str = warning_message
        self._warning_message_label: Label = Label(vexpand=True, hexpand=True)

        set_widget_margin(frame, DISPLAY_WIDTH * 0.005)
        set_widget_margin(self._main_box, DISPLAY_WIDTH * 0.005)
        set_widget_margin(self._image_label_box, DISPLAY_WIDTH * 0.005)
        set_widget_margin(image_label_frame, DISPLAY_WIDTH * 0.005)
        self._main_box.append(image_label_frame)
        self.set_child(frame)
        self._setup_warning_dialog()


    def _setup_warning_dialog(self) -> None:
        """
        _setup_warning_dialog

        Make the initial widgets setup.

        :return:
        """

        self._setup_warning_image()
        self._setup_warning_message()
        self._setup_ok_button()


    def show_all(self) -> None:
        """
        show_all

        Draws the warning dialog and its widgets.

        :return:
        """

        self.set_visible(True)


    def set_warning_message(self, text: str) -> None:
        """
        set_warning_message

        Sets the warning dialog's text.

        :param text: Text to set as the warning text for the warning dialog.
        :return:
        """

        self._warning_message = text

        self._warning_message_label.set_text(self._warning_message)


    def _setup_warning_image(self) -> None:
        """
        _setup_warning_image

        Setup the warning dialog's image.

        :return:
        """


        warning_gicon: Icon = Icon.new_for_string(
            path.join(ICONS_SYMBOLIC_DIRECTORY,
            "warning-symbolic.svg")
        )
        warning_image: Image = Image.new_from_gicon(warning_gicon)

        warning_image.set_pixel_size(int(DISPLAY_WIDTH * 0.05))
        set_widget_margin(warning_image, DISPLAY_WIDTH * 0.005)
        self._image_label_box.append(warning_image)


    def _setup_warning_message(self) -> None:
        """
        _setup_warning_message

        Setup the warning message.

        :return:
        """

        label_frame: Frame = Frame(child=self._warning_message_label)

        set_widget_margin(label_frame, DISPLAY_WIDTH * 0.005)
        self._image_label_box.append(label_frame)


    def _setup_ok_button(self) -> None:
        """
        _setup_ok_button

        Setup the ok button.

        :return:
        """

        ok_button = Button(label="Ok", halign=Align.CENTER, valign=Align.BASELINE_CENTER)
        ok_button_frame: Frame = Frame(child=ok_button)

        set_widget_margin(ok_button, DISPLAY_WIDTH * 0.005)
        set_widget_margin(ok_button_frame, DISPLAY_WIDTH * 0.005)
        self._main_box.append(ok_button_frame)
        ok_button.connect("clicked", lambda _: self.close())


__all__: list[str] = ["WarningDialog"]

