from __future__ import annotations

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository.Gtk import Dialog, Image, Label, ResponseType, STOCK_OK, Window, Box
from gi.repository.GdkPixbuf    import Pixbuf
from gi.repository.GLib         import Error as GLib_Error

from os import path

from asts.TypeAliases import Filepath
from asts.Utils       import setMargin


class AnkiDialog(Dialog):
    def __init__(self, parent: Window):
        super().__init__(title='Warning - Anki is open', transient_for=parent)

        self.set_default_size(width=250, height=100)
        self.set_modal(True)
        self.set_keep_above(True)
        self.set_decorated(False)
        self.set_urgency_hint(True)

        lbl: Label = Label(label='Warning: your anki is probably open, please close it before trying again.')
        box: Box   = self.get_content_area()

        setMargin(box, 20)

        # box.pack_(child, expand, fill, padding)
        box.pack_start(lbl, False, True, 0)

        img_path: Filepath = path.join(path.dirname(__file__), "..", 'Icons/delete.png')

        try:
            warn_pixbuf: Pixbuf = Pixbuf().new_from_file_at_scale(img_path, 50, 50, True)
            warn_img: Image = Image().new_from_pixbuf(warn_pixbuf)

            box.pack_start(warn_img, False, True, 0)
            setMargin(warn_img, 20)

        except GLib_Error:
            exit(f'{img_path} file not found. Failed to create pixbuf.')

        self.add_buttons(STOCK_OK, ResponseType.OK)


    def showAll(self) -> None:
        """
        Draws the dialog.

        :return:
        """

        self.show_all()
        self.run()
        self.destroy()

