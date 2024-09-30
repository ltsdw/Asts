from asts.custom_typing.globals import GTK_VERSION

from gi import require_version
require_version(*GTK_VERSION)
from gi.repository.Gtk import Application

from asts.interface.files_chooser_window import FilesChooserWindow


class Asts(Application):
    def __init__(self):
        super().__init__(application_id="com.github.ltsdw.asts")


    def do_activate(self):
        FilesChooserWindow(self).set_visible(True)


    def do_startup(self):
        Application.do_startup(self)


__all__: list[str] = ["Asts"]

