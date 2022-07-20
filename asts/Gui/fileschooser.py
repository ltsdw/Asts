from enum   import IntEnum
from os     import path
from typing import List, Optional

from gi     import require_version

require_version('GdkPixbuf', '2.0')

from gi.repository.Gdk       import RGBA
from gi.repository.GdkPixbuf import Pixbuf
from gi.repository.GLib      import Error as GLib_Error
from gi.repository.GLib      import timeout_add

require_version('Gtk', '3.0')

from gi.repository.Gtk import (
    Align,
    Application,
    Box,
    Button,
    Entry,
    FileChooser,
    FileChooserButton,
    FileFilter,
    Grid,
    Label,
    Image,
    Orientation,
    StateFlags,
    Window
)

from asts.Gui           import CardsGenerator
from asts.TypeAliases   import Filename, Filepath

from asts.Utils         import (
    clearCachedFiles,
    createCacheDirIfItNotExists,
    isCollection,
    isSub,
    isVideo,
    recentUsedFiles,
    setMargin
)


class FileType(IntEnum):
    ANKI2_COLLECTION= 0
    VIDEO           = 1
    SUBTITLE        = 2
    O_SUBTITLE      = 3


class FilesChooser(Window):
    def __init__(self, app: Application):
        super().__init__(title='Asts', application=app)
        
        self._app: Application = app

        self.set_default_size(1000, 700)
        self.set_keep_above(True)
        self.set_resizable(False)

        self._box: Box = Box()
        self._box.set_orientation(Orientation.VERTICAL)

        setMargin(self._box, 10)

        self._fst_grid: Grid = Grid()

        # labels
        self._setLabels()

        # file choosers button
        # _fc_s[0] = anki2.collection file
        # _fc_s[1] = video file
        # _fc_s[2] = subtitle file
        # _fc_s[3] = optional subtitle file
        self._fc_s: List[FileChooser] = self._setFileChoosers()

        # text entry
        self._entry: Entry
        self._setTextEntry()

        self._fillCachedFile()

        # filters
        self._setFilters()

        # buttons
        self._next_btn: Button
        self._setButtonsSignals()

        # box.pack_(child, expand, fill, padding)
        self._box.pack_start(self._fst_grid, False, True, 0)

        self.add(self._box)

    def _setLabels(self) -> None:
        """
        Setup the labels for the grid.

        :return:
        """

        labels: List[Label] = [
            Label(label='collection.anki2 File (Required):'),
            Label(label='Video (Required):'),
            Label(label='Subtitle File with The Target Language (Required):'),
            Label(label='Subtitle File with Translation (Optional):'),
            Label(label='Deck Name (Required):')
        ]

        for (idx, lbl) in enumerate(labels):
            lbl.set_halign(Align.START)

            # Grid.attach(child, left, top, width, height)
            self._fst_grid.attach(lbl, 0, idx, 1, 1)

    def _setFileChoosers(self) -> List[FileChooser]:
        """
        Set up the file choosers for the grid.

        :return: The file choosers created.
        """

        f_cs: List[FileChooser] = [
            FileChooserButton() for _ in range(4)
        ]

        for (idx, f_c) in enumerate(f_cs):
            f_c.set_hexpand(True)
            setMargin(f_c, 10, 5, 10, 5)

            f_c.set_halign(Align.FILL)

            self._fst_grid.attach(f_c, 1, idx, 1, 1)
        
        return f_cs

    def _setFilters(self) -> None:
        """
        Set a filter for each file chooser.

        :return: 
        """

        ff1: FileFilter = FileFilter()
        ff1.set_name('collection.anki2')
        ff1.add_pattern('*.anki2')

        self._fc_s[FileType.ANKI2_COLLECTION].add_filter(ff1)

        ff2: FileFilter = FileFilter()
        ff2.set_name('Video File')
        ff2.add_mime_type('video/mp4')
        ff2.add_mime_type('video/wmv')
        ff2.add_mime_type('video/avi')
        ff2.add_mime_type('video/mkv')
        ff2.add_mime_type('video/webm')
        ff2.add_pattern('*.mp4')
        ff2.add_pattern('*.wmv')
        ff2.add_pattern('*.avi')
        ff2.add_pattern('*.mkv')
        ff2.add_pattern('*.webm')

        self._fc_s[FileType.VIDEO].add_filter(ff2)

        ff3: FileFilter = FileFilter()
        ff3.set_name('Subtitles (ASS/SRT)')
        ff3.add_pattern('*.srt')
        ff3.add_pattern('*.ass')

        self._fc_s[FileType.SUBTITLE].add_filter(ff3)
        self._fc_s[FileType.O_SUBTITLE].add_filter(ff3)


    def _fillCachedFile(self) -> None:
        """
        Fills up collection_file and deck_name filename.

        :return:
        """

        try:
            cache_dir: Filepath = path.abspath('data/cache')
            cached_usage: Filename   = path.join(cache_dir + '/' + 'cached_usage.txt') 

            with open(cached_usage, 'r') as f:
                list_cache: List[str] = f.read().split('\n')
                self._fc_s[FileType.ANKI2_COLLECTION].set_filename(list_cache[0])
                self._entry.set_text(list_cache[1])
        # it's safe to pass here
        # it means that there's no filename cached to be used
        except FileNotFoundError:
            pass

    def _setButtonsSignals(self) -> None:
        """
        Set up the buttons and their respective signals for both grids.

        :param win: A window.
        :param fst_grid: The first grid container where the buttons goes in.
        :param box: The box container where the first grid goes in.
        :param fc_s: A list with file choosers.
        :return:
        """

        del_img: Optional[Pixbuf]

        img_path: Filepath = path.join(path.dirname(__file__), "..", 'Icons/delete.png')

        try:
            del_img = Pixbuf().new_from_file_at_scale(img_path, 20, 20, False)
        except GLib_Error:
            exit(f'{img_path} file not found. Failed to create pixbuf.')

        icons: List[Optional[Image]] = [ Image().new_from_pixbuf(del_img) for _ in range(4) ]

        btns: List[Button] = [ Button() for _ in range(4) ]

        for (idx, btn) in enumerate(btns):
            btn.set_image(icons[idx])
            setMargin(btn, 0, 5, 0, 5)
            btn.set_halign(Align.END)

            self._fst_grid.attach(btn, 2, idx, 1, 1)

        btns[FileType.ANKI2_COLLECTION].connect(
            'clicked', lambda _: self._fc_s[FileType.ANKI2_COLLECTION].unselect_all()
        )

        btns[FileType.VIDEO].connect(
            'clicked', lambda _: self._fc_s[FileType.VIDEO].unselect_all()
        )

        btns[FileType.SUBTITLE].connect(
            'clicked', lambda _: self._fc_s[FileType.SUBTITLE].unselect_all()
        )

        btns[FileType.O_SUBTITLE].connect(
            'clicked', lambda _: self._fc_s[FileType.O_SUBTITLE].unselect_all()
        )

        box: Box = Box()

        self._box.pack_end(box, False, True, 0)

        box.set_orientation(Orientation.HORIZONTAL)
        box.set_halign(Align.CENTER)

        cancel_btn: Button = Button(label='Cancel')

        box.pack_start(cancel_btn, False, True, 0)

        cancel_btn.set_margin_bottom(10)
        cancel_btn.connect('clicked', lambda _: self.close())


        self._next_btn = Button(label='Next')

        box.pack_end(self._next_btn, False, True, 0)

        setMargin(self._next_btn, 200, 10, 0, 0)
        self._next_btn.connect('clicked', self._onNextBtnClicked)

        
        timeout_add(300, self._setSensitiveNextBtn)
        timeout_add(300, self._checkInvalidSelection)

    def _setTextEntry(self) -> None:
        """
        Sets the text entry for deck name.

        :return:
        """

        self._entry = Entry(placeholder_text='Deck name...')

        setMargin(self._entry, 10, 5, 10, 5)

        self._fst_grid.attach(self._entry, 1, 4, 1, 1)

    def _getFilename(self, f_type: FileType) -> Optional[str]:
        """
        Return the name of the file.

        :param f_type: The type of file.
        :return: The name of the file.
        """

        try:
            return self._fc_s[f_type].get_filename()
        except IndexError:
            return None

    def _getDeckName(self) -> str:
        """
        Gets the deck name.

        :return: The deck name.
        """

        return self._entry.get_text()

    def _checkInvalidSelection(self) -> bool:
        """
        Unselects any invalid filename selected through file choosers.

        :return: True to keep timeout_add running.
        """

        col: Optional[str]   = self._getFilename(FileType.ANKI2_COLLECTION)
        vid: Optional[str]   = self._getFilename(FileType.VIDEO)
        sub: Optional[str]   = self._getFilename(FileType.SUBTITLE)
        o_sub: Optional[str] = self._getFilename(FileType.O_SUBTITLE)

        if col != None and not isCollection(col):
            self._fc_s[0].unselect_all()
        
        if vid != None and not isVideo(vid):
            self._fc_s[1].unselect_all()

        if sub != None and not isSub(sub):
            self._fc_s[2].unselect_all()

        if o_sub != None and not isSub(o_sub):
            self._fc_s[3].unselect_all()

        return True

    def _setSensitiveNextBtn(self) -> bool:
        """
        Set if a button is clickable or not.

        :return: True to keep timeout_add running.
        """

        col: bool       = isCollection(self._getFilename(FileType.ANKI2_COLLECTION))
        vid: bool       = isVideo(self._getFilename(FileType.VIDEO))
        sub: bool       = isSub(self._getFilename(FileType.SUBTITLE))
        deck_name: str  = self._getDeckName()

        if all((col, vid, sub, deck_name)):
            self._next_btn.set_sensitive(True)
        else:
            self._next_btn.set_sensitive(False)

        return True

    def _onNextBtnClicked(self, _) -> None:
        """
        Opens the generator of anki cards.

        :return:
        """

        createCacheDirIfItNotExists()

        clearCachedFiles()

        recentUsedFiles(
            self._getFilename(FileType.ANKI2_COLLECTION),
            self._getDeckName()
        )

        CardsGenerator(
            self,
            self._app,
            self._getFilename(FileType.ANKI2_COLLECTION),
            self._getFilename(FileType.VIDEO),
            self._getFilename(FileType.SUBTITLE),
            self._getFilename(FileType.O_SUBTITLE),
            self._getDeckName()
        ).showAll()

