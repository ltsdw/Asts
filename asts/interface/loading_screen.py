from asts.custom_typing.globals import GTK_VERSION

from gi import require_version
require_version(*GTK_VERSION)
from gi.repository.Gtk import (
    Align, Box, Frame, Orientation, Spinner,
    Window
)
from asts.custom_typing.globals import DISPLAY_WIDTH, DISPLAY_HEIGHT


class LoadingScreen(Window):
    def __init__(self, parent: Window) -> None:
        """
        LoadingScreen

        Simple loading screen.

        :param parent: The parent window where the button is placed.
        :return:
        """

        super().__init__(
            title="Loading",
            transient_for=parent,
            modal=True,
            resizable=False,
            decorated=False,
            hide_on_close=True,
        )

        self.set_default_size(int(DISPLAY_WIDTH * 0.35), int(DISPLAY_HEIGHT * 0.35))

        self._main_box: Box = Box(
            orientation=Orientation.VERTICAL,
            valign=Align.CENTER,
            halign=Align.CENTER
        )
        self._main_frame: Frame = Frame(child=self._main_box)
        self._spinner: Spinner = Spinner()

        self._spinner.set_size_request(int(DISPLAY_WIDTH * 0.05), int(DISPLAY_WIDTH * 0.05))
        self._main_box.append(self._spinner)
        self.set_child(self._main_frame)


    def show_loading_screen(self):
        """
        show_loading_screen

        Show the loading screen.

        :return:
        """

        self._spinner.start()
        self.set_visible(True)


    def hide_loading_screen(self):
        """
        hide_loading_screen

        Hides the loading screen.

        :return:
        """

        self.set_visible(False)


__all__: list[str] = ["LoadingScreen"]

