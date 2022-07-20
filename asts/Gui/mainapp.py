from gi import require_version

require_version('Gtk', '3.0')

from gi.repository.Gtk import Application

from asts.Gui import FilesChooser

class MainApp(Application):
    def __init__(self):
        super().__init__(application_id='asts.Gui.mainapp')

    def do_activate(self):
        FilesChooser(self).show_all()

    def do_startup(self):
        Application.do_startup(self)

