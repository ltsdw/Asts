from __future__ import annotations

from typing             import Dict, List, Optional, Tuple
from concurrent.futures import Future

from gi import require_version

require_version('Gtk', '3.0')

from gi.repository.Gtk import (
    Align,
    Application,
    Box,
    Button,
    CellRendererText,
    CellRendererToggle,
    CheckButton,
    ColorButton,
    Grid,
    Label,
    ListStore,
    Orientation,
    ProgressBar,
    ScrolledWindow,
    SearchEntry,
    SeparatorToolItem,
    TextBuffer,
    TextIter,
    TextMark,
    TextTag,
    TextTagTable,
    TextView,
    Toolbar,
    ToolButton,
    ToolItem,
    TreePath,
    TreeSelection,
    TreeView,
    TreeViewColumn,
    TreeViewColumnSizing,
    TreeViewGridLines,
    Window
)

from gi.repository.GLib import idle_add, timeout_add

from gi.repository.Pango import Style, Underline, Weight

from asts.Utils import (
    deserializeIt,
    extractAllDialogues,
    serializeIt,
    setMargin
)

from asts.TypeAliases import *


class CardsGenerator(Window):
    def __init__(
        self,
        parent: Window,
        app: Application,
        col_filename: Filename,
        vid_filename: Filename,
        sub_filename: Filename,
        opt_sub_filename: OptFilename,
        deck_name: str
    ):

        super().__init__(title='Asts - Anki Card Generator', application=app, transient_for=parent)

        self.set_default_size(width=1000, height=700)
        self.set_keep_above(True)
        self.set_modal(True)
        self.set_resizable(False)

        self._main_box: Box = Box()
        self._main_box.set_orientation(Orientation.VERTICAL)
        setMargin(self._main_box, 10)

        self.add(self._main_box)

        self._subtitles_grid: Grid = Grid()
        setMargin(self._subtitles_grid, 5)

        # box.pack_(expand, fill, padding)
        self._main_box.pack_start(self._subtitles_grid, False, True, 0)

        self._collection_filename: Filename         = col_filename
        self._video_filename: Filename              = vid_filename
        self._subtitles_filename: Filename          = sub_filename
        self._opt_subtitles_filename: OptFilename   = opt_sub_filename
        self._deck_name: str                        = deck_name

        self._any_media_toggled: bool = False
        self._dict_any_media: Dict[str, bool]

        self._dict_any_change_front: Dict[str, bytes]
        self._dict_any_change_back: Dict[str, bytes]

        self._textview_front: TextView
        self._textview_back: TextView

        self._textbuffer_front: TextBuffer
        self._textbuffer_back: TextBuffer

        self._subtitles_liststore: ListStore
        self._subtitles_liststore_back: ListStore

        self._subtitles_treeview: TreeView

        self._selected_row: TreeSelection

        self._progress_bar: ProgressBar

        self._cancel_btn: Button
        self._generate_btn: Button

        self._cur_progress: int
        self._max_tasks: int

        self._cancel_task: bool

        self._list_of_sentences: ListSentences
        self._list_info_medias: List[List[Info]]

        self._color_tag_names: List[str]
        # TheadingHandler will utilize these
        # updating the status for each task tasks
        # also the sensitive and progress of the progress bar
        # depends on these.
        self._futures_list: List[Future]

    def showAll(self) -> None:
        """
        Draws the cards generator window and it's respective widgets.

        :return:
        """

        # subtitles tree view
        self._setSubtitleTreeView()

        # indice and dialogue cells
        self._setDialogCells()

        # start and end timer cells
        self._setTimerCells()

        # video, audio and image cells
        self._setMediasCells()

        # fills both tree view with the subtitles
        self._populateListStore()

        # setting the model after and initializing _selected_row and _dict_any_media
        # after the liststore being complete initialized
        self._subtitles_treeview.set_model(self._subtitles_liststore)

        self._selected_row = self._subtitles_treeview.get_selection()
        self._selected_row.connect('changed', self._itemSelected)

        self._dict_any_media = {str(key): False for key in enumerate(self._subtitles_liststore)}

        # search entry
        self._setSearchEntry()

        # sets up the sentence editing related (e.g toolbar, tagging, etc)
        self._setSentenceRelated()

        # all color tags are named as it's respective values
        self._color_tag_names = [
            '#9999c1c1f1f1', '#6262a0a0eaea', '#35358484e4e4', '#1c1c7171d8d8', '#1a1a5f5fb4b4',
            '#8f8ff0f0a4a4', '#5757e3e38989', '#3333d1d17a7a', '#2e2ec2c27e7e', '#2626a2a26969',
            '#f9f9f0f06b6b', '#f8f8e4e45c5c', '#f6f6d3d32d2d', '#f5f5c2c21111', '#e5e5a5a50a0a',
            '#ffffbebe6f6f', '#ffffa3a34848', '#ffff78780000', '#e6e661610000', '#c6c646460000',
            '#f6f661615151', '#eded33333b3b', '#e0e01b1b2424', '#c0c01c1c2828', '#a5a51d1d2d2d',
            '#dcdc8a8adddd', '#c0c06161cbcb', '#91914141acac', '#81813d3d9c9c', '#616135358383',
            '#cdcdabab8f8f', '#b5b583835a5a', '#98986a6a4444', '#86865e5e3c3c', '#636345452c2c',
            '#ffffffffffff', '#f6f6f5f5f4f4', '#dededddddada', '#c0c0bfbfbcbc', '#9a9a99999696',
            '#777776767b7b', '#5e5e5c5c6464', '#3d3d38384646', '#24241f1f3131', '#000000000000',
        ]

        # sets up dictionary used to track the tags used
        self._initDictionariesTag()

        # sets up the buttons to select all sentences
        self._setSelectAll()

        # sets up the progress bar
        self._setProgressBar()

        # cancel and generate buttonsj
        self._resetFuturesLists()
        self._setButtons()

        self.show_all()

    def _resetFuturesLists(self) -> None:
        """
        Assign a empty list of both lists of futures (futures_setences and futures_medias).

        :return:
        """

        self._futures_list = []

    def _setSearchEntry(self) -> None:
        """
        Connect the changed event for the search_entry object.

        :return:
        """

        search_entry: SearchEntry = SearchEntry()
        search_entry.set_halign(Align.END)

        setMargin(search_entry, 0, 5, 0, 5)

        self._subtitles_grid.attach(search_entry, 0, 0, 1, 1)

        search_entry.connect('changed', self.searchIt)

    def searchIt(self, search_entry: SearchEntry) -> None:
        """
        Searchs over the _subtitles_liststore.

        :return:
        """

        term_searched: str = search_entry.get_text()

        for i, term in enumerate(self._subtitles_liststore):
            if term_searched and term_searched in term[1].lower():
                self._subtitles_treeview.set_cursor(i)
                break

    def _setSelectAll(self) -> None:
        """
        Sets up widgets to select all sentences.

        :return:
        """

        grid: Grid = Grid()
        grid.set_halign(Align.END)
        self._subtitles_grid.attach(grid, 0, 2, 1, 1)

        lbl: Label = Label(label='Select all')
        setMargin(lbl, 5)

        grid.attach(lbl, 0, 0, 1, 1)

        all_vid_toggle: CheckButton = CheckButton()
        all_vid_toggle.set_halign(Align.CENTER)
        all_vid_toggle.connect('toggled', self._onAllVideosToggled)

        setMargin(all_vid_toggle, 5)

        grid.attach(all_vid_toggle, 1, 0, 1, 1)

        lbl2: Label = Label(label='Videos')

        setMargin(lbl2, 5)

        grid.attach(lbl2, 1, 1, 1, 1)

        all_audio_toggle: CheckButton = CheckButton()
        all_audio_toggle.set_halign(Align.CENTER)
        all_audio_toggle.connect('toggled', self._onAllAudiosToggled, all_vid_toggle)

        setMargin(all_audio_toggle, 5)

        grid.attach(all_audio_toggle, 2, 0, 1, 1)

        lbl3: Label = Label(label='Audios')

        setMargin(lbl3, 5)

        grid.attach(lbl3, 2, 1, 1, 1)

        all_img_toggle: CheckButton = CheckButton()
        all_img_toggle.set_halign(Align.CENTER)
        all_img_toggle.connect('toggled', self._onAllImagesToggled)

        setMargin(all_img_toggle, 5)

        grid.attach(all_img_toggle, 3, 0, 1, 1)
        
        lbl4: Label = Label(label='Snapshot')

        setMargin(lbl4, 5)

        grid.attach(lbl4, 3, 1, 1, 1)

    def _onAllVideosToggled(self, _) -> None:
        """
        Handle the toggled event for the ToggleButton object.

        :param widget: ToggleButton object.
        :return:
        """

        for i in range(len(self._subtitles_liststore)):
            if self._subtitles_liststore[i][5]:

                self._subtitles_liststore[i][5] = not self._subtitles_liststore[i][5]
                self._subtitles_liststore[i][4] = not self._subtitles_liststore[i][4]
                self._dict_any_media[str(i)]    = self._subtitles_liststore[i][4]

            elif self._subtitles_liststore[i][6]:

                self._subtitles_liststore[i][6] = not self._subtitles_liststore[i][6]
                self._subtitles_liststore[i][4] = not self._subtitles_liststore[i][4]
                self._dict_any_media[str(i)]    = self._subtitles_liststore[i][4]

            else:
                self._subtitles_liststore[i][4] = not self._subtitles_liststore[i][4]
                self._dict_any_media[str(i)]    = self._subtitles_liststore[i][4]

        if True in self._dict_any_media.values():
            self._any_media_toggled = True
        else:
            self._any_media_toggled = False

    def _onAllAudiosToggled(self, _) -> None:
        """
        Handle the toggled event for the ToggleButton object.

        :param widget: ToggleButton object.
        :return:
        """

        for i in range(len(self._subtitles_liststore)):
            if self._subtitles_liststore[i][4]:

                self._subtitles_liststore[i][4] = not self._subtitles_liststore[i][4]
                self._subtitles_liststore[i][5] = not self._subtitles_liststore[i][5]
                self._dict_any_media[str(i)]    = self._subtitles_liststore[i][5]

            elif self._subtitles_liststore[i][5] and self._subtitles_liststore[i][6]:

                self._subtitles_liststore[i][5] = not self._subtitles_liststore[i][5]
                self._dict_any_media[str(i)]    = self._subtitles_liststore[i][6]

            else:
                self._subtitles_liststore[i][5] = not self._subtitles_liststore[i][5]
                self._dict_any_media[str(i)]    = self._subtitles_liststore[i][5]

        if True in self._dict_any_media.values():
            self._any_media_toggled = True
        else:
            self._any_media_toggled = False

    def _onAllImagesToggled(self, _) -> None:
        """
        Handle the toggled event for the ToggleButton object.

        :param widget: ToggleButton object.
        :return:
        """

        for i in range(len(self._subtitles_liststore)):
            if self._subtitles_liststore[i][4]:

                self._subtitles_liststore[i][4] = not self._subtitles_liststore[i][4]
                self._subtitles_liststore[i][6] = not self._subtitles_liststore[i][6]
                self._dict_any_media[str(i)]    = self._subtitles_liststore[i][6]

            else:
                self._subtitles_liststore[i][6] = not self._subtitles_liststore[i][6]
                self._dict_any_media[str(i)]    = self._subtitles_liststore[i][6]

        if True in self._dict_any_media.values():
            self._any_media_toggled = True
        else:
            self._any_media_toggled = False

    def _initDictionariesTag(self) -> None:
        """
        Init the default values for the used tags.

        :return:
        """

        # dictionaries to track the tags
        self._dict_any_change_front = (
            { str(key): serializeIt( text_buffer=self._textbuffer_front, tmp_string=value[1] )
              for key, value in enumerate(self._subtitles_liststore)
            }
        )

        self._dict_any_change_back = (
            { str(key): serializeIt( text_buffer=self._textbuffer_back, tmp_string=value[1] )
              for key, value in enumerate(self._subtitles_liststore_back)
            }
        )

    def _populateListStore(self) -> None:
        """
        Fills both list store (front and back) with subtitles.

        :return:
        """

        self._subtitles_liststore = ListStore(
            int,  # indice
            str,  # dialogue
            str,  # start timer
            str,  # end timer
            bool, # whether video is selected
            bool, # whether audio is selected
            bool  # whether image is selected
        )

        # only the first two values are important here
        self._subtitles_liststore_back = ListStore(int, str, str, str, bool, bool, bool)

        dialogues_list: List[List[Info]] = extractAllDialogues(self._subtitles_filename)

        for dialogue in dialogues_list:
            self._subtitles_liststore.append(dialogue)

        if self._opt_subtitles_filename:
            opt_dialogues_list: List[List[Info]] = extractAllDialogues(self._opt_subtitles_filename)

            # the subtitles and their respective translations
            # may or may not be of same lenght
            # in that case fill the list with dummy values
            for i in range(len(dialogues_list)):
                try:
                    self._subtitles_liststore_back.append(opt_dialogues_list[i])
                except IndexError:
                    self._subtitles_liststore_back.append((i, '', '', '', False, False, False))
        else:
            # in case no subtitles was selected for the back list store
            # fill it with dummy values
            for i in range(len(dialogues_list)):
                self._subtitles_liststore_back.append((i, '', '', '', False, False, False))

    def _setTimerCells(self) -> None:
        """
        Arrange the start and end timer cells.

        :return:
        """
        # Making some cells editable 'Start' and 'End' respectivily
        editable_start_field: CellRendererText = CellRendererText()
        editable_end_field: CellRendererText   = CellRendererText()

        editable_start_field.set_property('editable', True)
        editable_end_field.set_property('editable', True)

        self._subtitles_treeview.append_column(
            TreeViewColumn(title='Start', cell_renderer=editable_start_field, text=2)
        )

        self._subtitles_treeview.append_column(
            TreeViewColumn(title='End', cell_renderer=editable_end_field, text=3)
        )

        editable_start_field.connect('edited', self._startFieldEdited)
        editable_end_field.connect('edited', self._endFieldEdited)

    def _startFieldEdited(self, _, path: TreePath, text: str) -> None:
        """
        Handle the edited event for the start timer field cell.

        :widget: CellRendererText object.
        :path: TreePath object.
        :text: A string to be assigned to subtitles_liststore.
        :return:
        """

        from re import compile, Pattern


        regex_timer: Pattern[str] = compile(r'([0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9])')
        result = regex_timer.findall(text)

        if result:
            self._subtitles_liststore[path][2] = result[0]

    def _endFieldEdited(self, _, path: TreePath, text: str) -> None:
        """
        Handle the edited event for the end timer field cell.

        :widget: CellRendererText object.
        :path: TreePath object.
        :text: A string to be assigned to subtitles_liststore.
        :return:
        """

        from re import compile, Pattern


        regex_timer: Pattern[str] = compile(r'([0-9]?[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9])')
        result: List[str] = regex_timer.findall(text)

        if result:
            self._subtitles_liststore[path][3] = result[0]

    def _setDialogCells(self) -> None:
        """
        Arrange the dialogue and indice cell at the treeview.

        :return:
        """

        for i, title in enumerate(['Indice', 'Dialog']):
            renderer: CellRendererText  = CellRendererText()
            path_column: TreeViewColumn = TreeViewColumn(title=title, cell_renderer=renderer, text=i)

            if title == 'Dialog':
                path_column.set_sizing(TreeViewColumnSizing.FIXED)
                path_column.set_fixed_width(520)
                path_column.set_min_width(520)
            self._subtitles_treeview.append_column(path_column)

    def _setMediasCells(self) -> None:
        """
        Arrange the video, audio and snapshot cells.

        :return:
        """

        # cell video, audio and snapshot to toggle
        renderer_video_toggle: CellRendererToggle = CellRendererToggle()
        column_toggle = TreeViewColumn(title='Video', cell_renderer=renderer_video_toggle, active=4)
        self._subtitles_treeview.append_column(column_toggle)
        renderer_video_toggle.connect("toggled", self._onCellVideoToggled)

        renderer_audio_toggle: CellRendererToggle = CellRendererToggle()
        column_toggle = TreeViewColumn(title='Audio', cell_renderer=renderer_audio_toggle, active=5)
        self._subtitles_treeview.append_column(column_toggle)
        renderer_audio_toggle.connect("toggled", self._onCellAudioToggled)

        renderer_snapshot_toggle: CellRendererToggle = CellRendererToggle()
        column_toggle = TreeViewColumn(title='Snapshot', cell_renderer=renderer_snapshot_toggle, active=6)
        self._subtitles_treeview.append_column(column_toggle)
        renderer_snapshot_toggle.connect("toggled", self._onCellImageToggled)

    def _onCellVideoToggled(self, _, path) -> None:
        """
        Handles the toggled event for the CellRendererToggle object.
        
        :param widget: CellRendererToggle object.
        :path path: TreePath object.
        :return:
        """

        if self._subtitles_liststore[path][5]:

            self._subtitles_liststore[path][5] = not self._subtitles_liststore[path][5]
            self._subtitles_liststore[path][4] = not self._subtitles_liststore[path][4] 
            self._dict_any_media[path]         = self._subtitles_liststore[path][4]

        elif self._subtitles_liststore[path][6]:

            self._subtitles_liststore[path][6] = not self._subtitles_liststore[path][6]
            self._subtitles_liststore[path][4] = not self._subtitles_liststore[path][4]
            self._dict_any_media[path]         = self._subtitles_liststore[path][4]

        else:
            self._subtitles_liststore[path][4] = not self._subtitles_liststore[path][4]
            self._dict_any_media[path]         = self._subtitles_liststore[path][4]

        if True in self._dict_any_media.values():
            self._any_media_toggled = True
        else:
            self._any_media_toggled = False

    def _onCellAudioToggled(self, _, path: str) -> None:
        """
        Handles the toggled event for the CellRendererToggle object.
        
        :param widget: CellRendererToggle object.
        :path path: TreePath object.
        :return:
        """

        if self._subtitles_liststore[path][4]:

            self._subtitles_liststore[path][4] = not self._subtitles_liststore[path][4]
            self._subtitles_liststore[path][5] = not self._subtitles_liststore[path][5] 
            self._dict_any_media[path]         = self._subtitles_liststore[path][5]

        elif self._subtitles_liststore[path][5] and self._subtitles_liststore[path][6]:

            self._subtitles_liststore[path][5] = not self._subtitles_liststore[path][5]
            self._dict_any_media[path]         = self._subtitles_liststore[path][6]

        else:
            self._subtitles_liststore[path][5] = not self._subtitles_liststore[path][5]
            self._dict_any_media[path]         = self._subtitles_liststore[path][5]

        if True in self._dict_any_media.values():
            self._any_media_toggled = True
        else:
            self._any_media_toggled = False

    def _onCellImageToggled(self, _, path: str) -> None:
        """
        Handles the toggled event for the CellRendererToggle object.
        
        :param widget: CellRendererToggle object.
        :path path: TreePath object.
        :return:
        """

        if self._subtitles_liststore[path][4]:

            self._subtitles_liststore[path][4] = not self._subtitles_liststore[path][4]
            self._subtitles_liststore[path][6] = not self._subtitles_liststore[path][6] 
            self._dict_any_media[path]         = self._subtitles_liststore[path][6]

        elif self._subtitles_liststore[path][6] and self._subtitles_liststore[path][5]:

            self._subtitles_liststore[path][6] = not self._subtitles_liststore[path][6]
            self._dict_any_media[path]         = self._subtitles_liststore[path][5]

        else:
            self._subtitles_liststore[path][6] = not self._subtitles_liststore[path][6]
            self._dict_any_media[path]         = self._subtitles_liststore[path][6]

        if True in self._dict_any_media.values():
            self._any_media_toggled = True
        else:
            self._any_media_toggled = False

    def _setSubtitleTreeView(self) -> None:
        """
        Sets the scrolled window and a tree view for subtitles info.

        :return:
        """
 
        self._subtitles_treeview = TreeView()
        self._subtitles_treeview.set_grid_lines(TreeViewGridLines.BOTH)

        scrl_wnd: ScrolledWindow = ScrolledWindow()
        scrl_wnd.set_hexpand(True)
        scrl_wnd.set_vexpand(True)

        scrl_wnd.add(self._subtitles_treeview)

        self._subtitles_grid.attach(scrl_wnd, 0, 1, 1, 1)

    def _itemSelected(self, _) -> None:
        """
        Keeps tracks of selections change at the treeview object.

        :return:
        """

        path: str = self._selected_row.get_selected_rows()[1][0].to_string()

        deserializeIt(self._textbuffer_front, self._dict_any_change_front[path])
        deserializeIt(self._textbuffer_back, self._dict_any_change_back[path])

        self._textbuffer_front.connect('changed', self._editingCard)
        self._textbuffer_back.connect('changed', self._editingCardBack)

    def _editingCard(self, textbuffer_front: TextBuffer) -> None:
        """
        Keeps track of changes at the text_buffer_front.

        :param text_buffer_front: TextBuffer object.
        :return:
        """

        path: TreePath                     = self._selected_row.get_selected_rows()[1][0]
        start_iter_front: TextIter         = textbuffer_front.get_start_iter()
        end_iter_front: TextIter           = textbuffer_front.get_end_iter()
        self._subtitles_liststore[path][1] = textbuffer_front.get_text(start_iter_front, end_iter_front, True)

        self._dict_any_change_front[path.to_string()] = serializeIt(text_buffer=textbuffer_front)

    def _editingCardBack(self, textbuffer_back: TextBuffer) -> None:
        """
        Keeps track of changes at the text_buffer_back.

        :param text_buffer_back: TextBuffer object.
        :return:
        """

        path: TreePath                          = self._selected_row.get_selected_rows()[1][0]
        start_iter_back: TextIter               = textbuffer_back.get_start_iter()
        end_iter_back: TextIter                 = textbuffer_back.get_end_iter() 
        self._subtitles_liststore_back[path][1] = textbuffer_back.get_text(start_iter_back, end_iter_back, True)

        self._dict_any_change_back[path.to_string()] = serializeIt(text_buffer=textbuffer_back)

    def _setSentenceRelated(self) -> None:
        """
        Sets up the sentence editing widgets related.
        Also initialize both text buffers.

        :return:
        """

        box: Box = Box()

        self._main_box.pack_start(box, False, True, 0)

        box.set_orientation(Orientation.VERTICAL)

        setMargin(box, 5)

        toolbar: Toolbar = Toolbar()

        box.pack_start(toolbar, False, True, 0)

        toolbar.set_halign(Align.END)
        setMargin(toolbar, 5)

        lbl: Label = Label()
        lbl.set_markup('<i><b>Front</b></i>')

        box.pack_start(lbl, False, True, 0)

        lbl.set_halign(Align.START)
        setMargin(lbl, 5)

        scrl_wnd: ScrolledWindow = ScrolledWindow()
        scrl_wnd.set_hexpand(True)
        scrl_wnd.set_vexpand(True)

        textview: TextView = TextView()
        scrl_wnd.add(textview)

        box.pack_start(scrl_wnd, False, True, 0)

        self._textbuffer_front = textview.get_buffer()

        lbl2: Label = Label()
        lbl2.set_halign(Align.START)
        lbl2.set_markup('<i><b>Back</b></i>')

        box.pack_start(lbl2, False, True, 0)
        setMargin(lbl2, 5)

        scrl_wnd2: ScrolledWindow = ScrolledWindow()
        scrl_wnd2.set_hexpand(True)
        scrl_wnd2.set_vexpand(True)

        textview2: TextView = TextView()
        scrl_wnd2.add(textview2)

        box.pack_end(scrl_wnd2, False, True, 0)

        self._textbuffer_back = textview2.get_buffer()

        # this depends on the text buffer to be initialized
        self._setToolbarColorButton(toolbar)

        toolbar.insert(SeparatorToolItem(), 3)

        self._setToolbarUnderlineButton(toolbar)
        self._setToolbarBoldButton(toolbar)
        self._setToolbarItalicButton(toolbar)

        toolbar.insert(SeparatorToolItem(), 7)

        self._setToolbarTagRemoverButton(toolbar)

    def _setToolbarColorButton(self, toolbar: Toolbar) -> None:
        """
        Sets up the color button from the toolbar.

        :param toolbar: Toolbar object
        :return:
        """

        set_color_button: ToolButton    = ToolButton()
        set_color_button.set_icon_name('gtk-select-color')
        toolbar.insert(set_color_button, 1)

        tool_item_color_button: ToolItem= ToolItem()
        color_button                    = ColorButton()

        tool_item_color_button.add(color_button)
        toolbar.insert(tool_item_color_button, 2)

        set_color_button.connect('clicked', self._onToolbarColorBtnClicked, color_button)

    def _setToolbarUnderlineButton(self, toolbar: Toolbar) -> None:
        """
        Sets up the underline button from the toolbar.

        :param toolbar: Toolbar object
        :return:
        """

        tag_underline_front: TextTag    = self._textbuffer_front.create_tag('underline', underline=Underline.SINGLE)
        tag_underline_back: TextTag     = self._textbuffer_back.create_tag('underline', underline=Underline.SINGLE)
        button_underline: ToolButton    = ToolButton()

        button_underline.set_icon_name('format-text-underline-symbolic')
        toolbar.insert(button_underline, 4)

        button_underline.connect('clicked', self._onToolbarTagBtnClicked, tag_underline_front, tag_underline_back)

    def _setToolbarBoldButton(self, toolbar: Toolbar) -> None:
        """
        Sets up the bold button from the toolbar.

        :param toolbar: Toolbar object
        :return:
        """

        tag_bold_front: TextTag = self._textbuffer_front.create_tag('bold', weight=Weight.BOLD)
        tag_bold_back: TextTag  = self._textbuffer_back.create_tag('bold', weight=Weight.BOLD)
        button_bold: ToolButton = ToolButton()

        button_bold.set_icon_name('format-text-bold-symbolic')
        toolbar.insert(button_bold, 5)

        button_bold.connect('clicked', self._onToolbarTagBtnClicked, tag_bold_front, tag_bold_back)

    def _setToolbarItalicButton(self, toolbar: Toolbar) -> None:
        """
        Sets up the italic button from the toolbar.

        :param toolbar: Toolbar object
        :return:
        """

        tag_italic_front: TextTag = self._textbuffer_front.create_tag('italic', style=Style.ITALIC)
        tag_italic_back: TextTag  = self._textbuffer_back.create_tag('italic', style=Style.ITALIC)

        button_italic: ToolButton = ToolButton()
        button_italic.set_icon_name('format-text-italic-symbolic')
        toolbar.insert(button_italic, 6)

        button_italic.connect('clicked', self._onToolbarTagBtnClicked, tag_italic_front, tag_italic_back)

    def _setToolbarTagRemoverButton(self, toolbar: Toolbar) -> None:
        """
        Sets up the tag remover button from the toolbar.

        :param toolbar: Toolbar object.
        :return:
        """

        button_remove_all_tags: ToolButton  = ToolButton()

        button_remove_all_tags.set_icon_name('edit-clear-symbolic')
        toolbar.insert(button_remove_all_tags, 8)

        button_remove_all_tags.connect('clicked', lambda _: self._removeAllTagsFromSelection())

    def _getBounds(self) -> Tuple[TextMark, TextMark, Optional[str]]:
        """
        Returns the selection of the text in the text buffer.

        :return: A tuple with the textiter of the selection and the path string.
        """

        path: Optional[str]

        # if no row is selected
        # a IndexError will be raised
        try:
            path = self._selected_row.get_selected_rows()[1][0].to_string()
        except IndexError:
            path = None

        bounds_front: TextMark = self._textbuffer_front.get_selection_bounds()
        bounds_back: TextMark = self._textbuffer_back.get_selection_bounds()

        return (bounds_front, bounds_back, path)

    def _onToolbarColorBtnClicked(
            self,
            _,
            color_button: ColorButton) -> None:
        """
        Handles the clicked event for the tool_item_color_button.

        :param set_color_button: ToolButton object.
        :param color_button: ColorButton object.
        :return:
        """

        start: TextIter
        end: TextIter
        bounds_front: TextMark
        bounds_back: TextMark
        path: Optional[str]

        color: str                      = color_button.get_color().to_string()

        tag_table_front: TextTagTable   = self._textbuffer_front.get_tag_table()
        tag_table_back: TextTagTable    = self._textbuffer_back.get_tag_table()

        (bounds_front, bounds_back, path) = self._getBounds()

        # no selected row so there's nothing to do
        if not path:
            return

        ##### FRONT
        if bounds_front:
            (start, end) = bounds_front

            # only the first color applied to the selection
            # will be present at the final card
            # so remove all color previously applied to the current selected text.
            self._removeAllTagsFromSelection(color_tags=True)

            if not tag_table_front.lookup(color):
                tag_front: TextTag = self._textbuffer_front.create_tag(color, foreground=color)
                self._textbuffer_front.apply_tag(tag_front, start, end)
            else:
                self._textbuffer_front.apply_tag_by_name(color, start, end)

            self._dict_any_change_front[path] = serializeIt(text_buffer=self._textbuffer_front)

        ###### BACK
        if bounds_back:
            (start, end) = bounds_back

            # only the first color applied to the selected text
            # will be present at the final card
            # so remove all color previously applied to the current selected text.
            self._removeAllTagsFromSelection(color_tags=True)

            if not tag_table_back.lookup(color):
                tag_back       = self._textbuffer_back.create_tag(color, foreground=color)
                self._textbuffer_back.apply_tag(tag_back, start, end)
            else:
                self._textbuffer_back.apply_tag_by_name(color, start, end)

            self._dict_any_change_back[path] = serializeIt(text_buffer=self._textbuffer_back)

    def _onToolbarTagBtnClicked(
            self,
            _,
            tag_front: TextTag,
            tag_back: TextTag) -> None:
        """
        Handles the clicked event for the tool button. 

        :param widget: ToolButton object.
        :param tag_front: TextTag object.
        :param tag_back: TextTag object.
        :return:
        """

        start: TextIter
        end: TextIter
        bounds_front: TextMark
        bounds_back: TextMark
        path: Optional[str]

        (bounds_front, bounds_back, path) = self._getBounds()

        # no selected row so there's nothing to do
        if not path:
            return

        ##### FRONT
        if bounds_front:
            (start, end) = bounds_front

            self._textbuffer_front.apply_tag(tag_front, start, end)

            self._dict_any_change_front[path] = serializeIt(text_buffer=self._textbuffer_front)

        ###### BACK
        if bounds_back:
            (start, end) = bounds_back
            self._textbuffer_back.apply_tag(tag_back, start, end)

            self._dict_any_change_back[path] = serializeIt(text_buffer=self._textbuffer_back)

    def _removeAllTagsFromSelection(self, color_tags: bool = False) -> None:
        """
        Remove all tags from the current selected text.

        :param color_tags: If true only removes color tags.
        :return:
        """

        start: TextIter
        end: TextIter
        bounds_front: TextMark
        bounds_back: TextMark
        path: Optional[str]

        tag_table_front: TextTagTable   = self._textbuffer_front.get_tag_table()
        tag_table_back: TextTagTable    = self._textbuffer_back.get_tag_table()

        (bounds_front, bounds_back, path) = self._getBounds()

        # no selected row so there's nothing to do
        if not path:
            return

        ### FRONT
        if bounds_front:
            (start, end) = bounds_front

            if color_tags:
                for c in self._color_tag_names:
                    if tag_table_front.lookup(c):
                        self._textbuffer_front.remove_tag_by_name(c, start, end)
            else:
                self._textbuffer_front.remove_all_tags(start, end)
        
            self._dict_any_change_front[path] = serializeIt(text_buffer=self._textbuffer_front)

        ### BACK
        if bounds_back:
            (start, end) = bounds_back

            if color_tags:
                for c in self._color_tag_names:
                    if tag_table_back.lookup(c):
                        self._textbuffer_back.remove_tag_by_name(c, start, end)
            else:
                self._textbuffer_back.remove_all_tags(start, end)
 
            self._dict_any_change_back[path] = serializeIt(text_buffer=self._textbuffer_back)

    def _setProgressBar(self) -> None:
        """
        Sets up the progress bar.

        :return:
        """

        self._cur_progress = 0

        self._progress_bar = ProgressBar()

        setMargin(self._progress_bar, 5)

        self._main_box.pack_start(self._progress_bar, False, True, 0)

    def _setButtons(self) -> None:
        """
        Sets up the cancel and generate buttons.

        :return:
        """

        box: Box = Box()

        self._main_box.pack_end(box, False, True, 0)

        box.set_halign(Align.CENTER)
        box.set_orientation(Orientation.HORIZONTAL)

        setMargin(box, 5)

        self._cancel_btn = Button(label='Cancel')

        box.pack_start(self._cancel_btn, False, True, 0)

        setMargin(self._cancel_btn, 5, 5, 100, 5)
        self._cancel_btn.connect('clicked', self._onCancelBtnClicked)

        self._generate_btn = Button(label='Generate')

        box.pack_end(self._generate_btn, False, True, 0)

        setMargin(self._generate_btn, 100, 5, 5, 5)
        self._generate_btn.connect('clicked', self._onGenerateBtnClicked)

        timeout_add(300, self._setSensitiveGenerateBtn)

    def _setSensitiveGenerateBtn(self) -> bool:
        """
        Set the senstive for the generate_btn.

        :return: A boolean to signal whether idle_add should remove it from list event.
        """

        if self._cur_progress or not self._allFuturesDone():
            self._generate_btn.set_sensitive(False)
        elif not self._any_media_toggled:
            self._generate_btn.set_sensitive(False)
        else:
            self._generate_btn.set_sensitive(True)

        return True

    def _allFuturesDone(self) -> bool:
        """
        Check for the status of futures.

        :return: Return true if all futures are done.
        """

        for f in self._futures_list:
            if not f.done(): return False

        return True

    def _updateProgress(self) -> bool:
        """
        Keep track of the objects yet to be completed.
        Updates the progress bar.
        
        :param future: Parameter passed by add_done_callback.
        :return: a boolean to signal whether idle_add should remove it from list event.
        """

        if not self.getCancelTaskStatus():
            self._cur_progress += 1
            self._progress_bar.set_fraction(self._cur_progress / self._max_tasks)
            self._progress_bar.set_text(None)
            self._progress_bar.set_show_text(True)

            if self._cur_progress == self._max_tasks:
                self._cur_progress = 0
                self._progress_bar.set_text('Done!')
                self._progress_bar.set_show_text(True)

        return False

    def resetProgressbar(self) -> None:
        """
        Resets the progress bar back to zero.

        :return:
        """

        self._cur_progress = 0
        self._progress_bar.set_fraction(self._cur_progress)
        self._progress_bar.set_show_text(False)

    def idleaddUpdateProgress(self, _) -> None:
        """
        Call idle_add to call updateProgress.
        
        :param future: Optional future object.
        :return:
        """

        idle_add(self._updateProgress)

    def getCancelTaskStatus(self) -> bool:
        """
        Get the status for the cancel_task.

        :return: Return true if the task should be cancelled.
        """

        return self._cancel_task

    def setCancelTaskStatus(self, status: bool) -> None:
        """
        Set the status for the cancel_task.

        :return:
        """

        self._cancel_task = status

    def _idleaddUpdateProgress(self, _) -> None:
        """
        Call idle_add to call updateProgress.
        
        :param future: Optional future object.
        :return:
        """

        idle_add(self._updateProgress)

    def _setSensitiveCancelBtn(self) -> bool:
        """
        Set the sensitive for snd_cancel_button.

        :return:
        """

        if self._allFuturesDone():
            self._progress_bar.set_text('Canceled!')

            self._cancel_btn.set_sensitive(True)

            return False
        else:
            self._progress_bar.set_text('Cancelling please wait...')
            self._cancel_btn.set_sensitive(False)

        return True


    def _onCancelBtnClicked(self, _) -> None:
        """
        Handle the clicked event for the second_cancel_button button.

        :param widget: Button object.
        :return:
        """

        if not self._cur_progress:
            self._generate_btn.set_sensitive(True)
            self.close()
        else:
            self.setCancelTaskStatus(True)

            self._cur_progress = 0

            self._progress_bar.set_fraction(self._cur_progress)
            self._progress_bar.set_show_text(True)

            timeout_add(300, self._setSensitiveCancelBtn)

        self._cur_progress = 0
        self._progress_bar.set_fraction(self._cur_progress)

    def _onGenerateBtnClicked(self, _) -> None:
        """
        Handle the click event for the generate_btn.

        :return:
        """

        from asts.Threading import ThreadingHandler


        self._listMediasSentences()

        ThreadingHandler(self)

    def _listMediasSentences(self) -> None:
        """
        Create two lists and fill them with filenames and sentences.

        :return:
        """
        
        from uuid import uuid1

        from asts.Utils import PangoToHtml


        # case other tasks already had been scheduled
        self._resetFuturesLists()

        self._list_of_sentences = []
        self._list_info_medias = []

        p: PangoToHtml = PangoToHtml()

        for i in range(len(self._subtitles_liststore)):
            if self._subtitles_liststore[i][4] or self._subtitles_liststore[i][5] or self._subtitles_liststore[i][6]:
                # a unique id for each media, some images will conflict if it has the same name as a image
                # on anki media collection 
                uuid_media  = uuid1().int

                text_front: str  = p.feed(self._dict_any_change_front[str(i)])
                text_back: str   = p.feed(self._dict_any_change_back[str(i)])

                self._list_info_medias.append([str(uuid_media)] + (self._subtitles_liststore[i][1:]))

                if self._subtitles_liststore[i][4] and not self._subtitles_liststore[i][6]:
                    self._list_of_sentences.append(
                        (
                            text_front,
                            text_back,
                            f'{uuid_media}.mp4',
                            None,
                            None
                        )
                    )
                elif self._subtitles_liststore[i][5] and self._subtitles_liststore[i][6]:
                    self._list_of_sentences.append(
                        (
                            text_front,
                            text_back,
                            None,
                            f'{uuid_media}.mp3',
                            f'{uuid_media}.bmp'
                        )
                    )
                elif self._subtitles_liststore[i][5] and not self._subtitles_liststore[i][6]:
                    self._list_of_sentences.append(
                        (
                            text_front,
                            text_back,
                            None,
                            f'{uuid_media}.mp3',
                            None
                        )
                    )
                else:
                    self._list_of_sentences.append(
                        (
                            text_front,
                            text_back,
                            None,
                            None,
                            f'{uuid_media}.bmp'
                        )
                    )

        self._max_tasks = len(self._list_info_medias) + len(self._list_of_sentences)

    def getCollection(self) -> Filename:
        """
        Returns the filename for the anki2.collection.

        :return: Filename of the anki2.collection.
        """

        return self._collection_filename

    def getDeckName(self) -> str:
        """
        Returns the deck name.

        :return: Deck name.
        """

        return self._deck_name

    def getVideoFilename(self) -> Filename:
        """
        Returns the name of the video file.

        :return: Video filename.
        """

        return self._video_filename

    def getListInfoMedias(self) -> List[List[Info]]:
        """
        Returns a list with information about each media to be used at creating cards.

        :return: A list with information about each media.
        """

        return self._list_info_medias

    def getListOfSentences(self) -> ListSentences:
        """
        Returns a List with information about each sentence to be used at creating cards.

        :return: A list with information about each sentence.
        """

        return self._list_of_sentences

    def appendFuture(self, future: Future) -> None:
        """
        Append the future to _futures_list.

        :return:
        """

        self._futures_list.append(future)

