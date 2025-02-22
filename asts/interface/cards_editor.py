from asts.custom_typing.globals import GTK_VERSION, GLIB_VERSION, GOBJECT_VERSION

from gi import require_version
require_version(*GTK_VERSION)
require_version(*GLIB_VERSION)
require_version(*GOBJECT_VERSION)
from gi.repository.Gtk import (
    Align, Application, Box, Button, ColorDialog, ColumnView,
    ColumnViewColumn, CustomFilter, Entry, FilterChange, FilterListModel,
    Frame, Grid, INVALID_LIST_POSITION, Label, ListItem, ListScrollFlags,
    Image, Orientation, ProgressBar, ScrolledWindow,
    SearchEntry, Separator, SignalListItemFactory,
    SingleSelection,  StyleContext, STYLE_PROVIDER_PRIORITY_APPLICATION,
    TextBuffer, TextIter, TextTag, TextTagTable,
    TextView, Window, Widget
)
from gi.repository.Gdk      import RGBA as GdkRGBA
from gi.repository.Gio      import Icon, AsyncResult
from gi.repository.GLib     import idle_add, timeout_add
from gi.repository.Pango    import Style, Underline, Weight
from gi.repository.GObject  import ParamSpec, BindingFlags

from concurrent.futures import Future
from typing             import cast, Literal, Iterator
from os                 import path
from re                 import Match

from asts.custom_typing.globals import (
    DISPLAY_HEIGHT, DISPLAY_WIDTH,
    ICONS_SYMBOLIC_DIRECTORY, REGEX_TIMESTAMP_PATTERN
)
from asts.utils.core_utils import is_timestamp_within, handle_exception_if_any, NEW_LINE
from asts.utils.extra_utils import (
    extract_all_dialogues, get_tagged_text_from_text_buffer,
    set_widget_margin, apply_tagged_text_to_text_buffer
)
from asts.custom_typing.check_button_wrapper import CheckButtonWrapper
from asts.custom_typing.aliases import Filepath, OptionalFilepath, SelectionBounds
from asts.custom_typing.dialogue_info import DialogueInfo, DialogueInfoIndex
from asts.custom_typing.rgba import RGBA
from asts.custom_typing.row_selection import RowSelection
from asts.custom_typing.typed_list_store import TypedListStore
from asts.custom_typing.css_manager import CssManager
from asts.custom_typing.cards_editor_states import CardsEditorState, CardsEditorStates
from asts.cards_generator.cards_generator import CardsGenerator
from asts.interface.warning_dialog import WarningDialog


class CardsEditor(Window):
    def __init__(
        self,
        parent: Window,
        app: Application,
        collection_filepath: Filepath,
        video_filepath: Filepath,
        subtitles_filepath: Filepath,
        optional_subtitles_filepath: OptionalFilepath,
        deck_name: str
    ) -> None:
        """
        CardsEditor

        A graphical interface to edit cards before adding them to the Anki's collection.

        :param parent: Parent window.
        :param app: Application class object.
        :param collection_filepath: Path to Anki's collection file.
        :param video_filepath: Path to the video file.
        :param subtitles_filepath: Path to the subtitles file.
        :param optional_subtitles_filepath: Path to the optional subtitles file.
        :return:
        """

        super().__init__(title="Asts - Anki Card Editor", application=app, transient_for=parent)

        self._main_box: Box = Box()
        self._main_grid: Grid = Grid()
        self._main_frame: Frame = Frame(child=self._main_grid)
        self._currently_selected_color: RGBA                    = RGBA(0.5, 0.5, 0.5)
        self._collection_filepath: Filepath                     = collection_filepath
        self._video_filepath: Filepath                          = video_filepath
        self._subtitles_filepath: Filepath                      = subtitles_filepath
        self._optional_subtitles_filepath: OptionalFilepath     = optional_subtitles_filepath
        self._deck_name: str                                    = deck_name
        self._number_medias_toggled: int = 0
        self._front_field_text_buffer_handler_id: int
        self._back_field_text_buffer_handler_id: int
        self._front_field_text_buffer: TextBuffer
        self._back_field_text_buffer: TextBuffer
        self._front_field_list_store: TypedListStore[DialogueInfo]
        self._back_field_list_store: TypedListStore[DialogueInfo]
        self._dialogues_columnview: ColumnView
        self._selected_row: SingleSelection
        self._row_selection: RowSelection
        self._search_entry: SearchEntry
        self._progress_bar: ProgressBar
        self._cancel_button: Button
        self._generate_button: Button
        self._cards_editor_state: CardsEditorState = CardsEditorState()
        self._futures_list: list[Future[None]] = []

        self.set_resizable(False)
        self.set_modal(True)
        self.set_default_size(int(DISPLAY_WIDTH * 0.90), int(DISPLAY_HEIGHT * 0.90))
        self._main_box.set_orientation(Orientation.VERTICAL)
        set_widget_margin(self._main_box, DISPLAY_WIDTH * 0.005)
        self.set_child(self._main_box)
        self._main_box.append(self._main_frame)
        self._setup_cards_editor()


    def _setup_cards_editor(self) -> None:
        """
        _setup_cards_editor

        Make the initial widgets setup.

        :return:
        """

        fields_box: Box = Box(orientation=Orientation.VERTICAL)
        buttons_box: Box = Box(orientation=Orientation.HORIZONTAL, halign=Align.CENTER)
        buttons_frame: Frame = Frame(child=buttons_box)
        toolbar_box: Box = Box(orientation=Orientation.HORIZONTAL)
        toolbar_frame: Frame = Frame(child=toolbar_box, halign=Align.END)
        fields_frame: Frame = Frame(child=fields_box)
        self._row_selection = RowSelection(index=0)

        DialogueInfo.reset()
        self._populate_list_store()
        self._setup_dialogues_column_view()
        self._setup_search_entry()
        fields_box.append(toolbar_frame)
        self._setup_front_field(fields_box)
        self._setup_back_field(fields_box)
        self._setup_toolbar(toolbar_box)
        self._setup_progress_bar(fields_box)
        fields_box.append(buttons_frame)
        self._setup_cancel_button(buttons_box)
        self._setup_generate_button(buttons_box)
        self._force_emit_selection_changed(position=0, n_items=1)
        self._main_box.append(fields_frame)
        self._setup_select_all_medias_check_buttons()


    def show_all(self) -> None:
        """
        show_all

        Draws the cards editor window and it's respective widgets.

        :return:
        """

        self.set_visible(True)


    def _force_emit_selection_changed(
        self,
        position: int = INVALID_LIST_POSITION,
        n_items: int = 0
    ) -> None:
        """
        _force_emit_selection_changed

        Emits a forced selection-changed signal,
        useful for when the selection doesn't change or
        we just want to call _on_selection_changed method.

        :param position: Position to where the change happened,
                         defaults to INVALID_LIST_POSITION.
        :param n_items: Number of items which changed, defaults to 0.
        :return:
        """

        self._selected_row.emit("selection-changed", position, n_items)


    def _populate_list_store(self) -> None:
        """
        _populate_list_store

        Fills both list store (front and back) with subtitles.

        :return:
        """

        self._front_field_list_store = TypedListStore(DialogueInfo)
        self._back_field_list_store = TypedListStore(DialogueInfo)
        dialogues_list: list[DialogueInfo] = extract_all_dialogues(self._subtitles_filepath)
        opt_dialogues_list: list[DialogueInfo] = extract_all_dialogues(self._optional_subtitles_filepath)

        for dialogue in dialogues_list:
            self._front_field_list_store.append(dialogue)

        DialogueInfo.reset()

        # the subtitles and its respective translations
        # may or may not be of same lenght
        # in that case fill the list with dummy values
        dialogues_iter: Iterator[DialogueInfo] = dialogues_list.__iter__()
        optional_dialogues_iter: Iterator[DialogueInfo] = opt_dialogues_list.__iter__()
        dialogue_info: DialogueInfo | None = next(dialogues_iter, None)
        opt_dialogue_info: DialogueInfo | None = next(optional_dialogues_iter, None)
        optional_dialogue_info: DialogueInfo = DialogueInfo()

        while True:
            if not dialogue_info: break

            if not opt_dialogue_info:
                self._back_field_list_store.append(DialogueInfo())
                dialogue_info = next(dialogues_iter, None)

                continue

            start_timestamp: str = dialogue_info[DialogueInfoIndex.START_TIMESTAMP]
            end_timestamp: str = dialogue_info[DialogueInfoIndex.END_TIMESTAMP]
            optional_start_timestamp: str = opt_dialogue_info[DialogueInfoIndex.START_TIMESTAMP]
            optional_end_timestamp: str = opt_dialogue_info[DialogueInfoIndex.END_TIMESTAMP]

            if (is_timestamp_within(start_timestamp, end_timestamp, optional_start_timestamp)
            and is_timestamp_within(start_timestamp, end_timestamp, optional_end_timestamp)):
                optional_dialogue_info[DialogueInfoIndex.DIALOGUE] += (
                    f"{NEW_LINE}{opt_dialogue_info[DialogueInfoIndex.DIALOGUE]}"
                    if optional_dialogue_info[DialogueInfoIndex.DIALOGUE]
                    else f"{opt_dialogue_info[DialogueInfoIndex.DIALOGUE]}"
                )
                opt_dialogue_info = next(optional_dialogues_iter, None)

                continue
            else:
                self._back_field_list_store.append(optional_dialogue_info)
                optional_dialogue_info = DialogueInfo()
                dialogue_info = next(dialogues_iter, None)

                continue

        DialogueInfo.reset()


    def _setup_dialogues_column_view(self) -> None:
        """
        _setup_dialogues_column_view

        Sets a column view to display information from the DialogueInfo object in a grid-like style.

        :return:
        """

        self._selected_row = SingleSelection(autoselect=True, can_unselect=True)
        self._dialogues_columnview = ColumnView(
            show_column_separators=True,
            show_row_separators=True,
            reorderable=False,
            model=self._selected_row
        )
        scrolled_window: ScrolledWindow = ScrolledWindow(hexpand=True, vexpand=True, kinetic_scrolling=False)

        self._selected_row.connect("selection-changed", self._on_selection_changed)
        scrolled_window.set_child(self._dialogues_columnview)
        self._main_grid.attach(scrolled_window, 0, 1, 1, 1)
        self._set_column_view_columns()


    def _on_selection_changed(self, *_: object) -> None:
        """
        _on_selection_changed

        Handles the "selection-changed" signal from SingleSelection.

        :param selection_model: The object which emitted the signal.
        :param position: The first item that may have changed.
        :param n_items: The number of items with changes.
        :return:
        """

        row: DialogueInfo | None = cast(DialogueInfo | None, self._selected_row.get_selected_item())

        if not row:
            self._front_field_text_buffer.set_text("")
            self._back_field_text_buffer.set_text("")
            return

        index: int = row.get_index()

        if not self._row_selection.has_selection_updates_blocked:
            self._row_selection.index = index

        back: DialogueInfo = cast(DialogueInfo, self._back_field_list_store[index])
        self._disable_front_field_text_buffer_event_listening()
        apply_tagged_text_to_text_buffer(self._front_field_text_buffer, row[DialogueInfoIndex.DIALOGUE])
        self._enable_front_field_text_buffer_event_listening()
        self._disable_back_field_text_buffer_event_listening()
        apply_tagged_text_to_text_buffer(self._back_field_text_buffer, back[DialogueInfoIndex.DIALOGUE])
        self._enable_back_field_text_buffer_event_listening()


    def _set_column_view_columns(self) -> None:
        """
        _set_column_view_columns

        Arrange columns and rows of the ColumnView object to match the properties of DialogueInfo.

        :return:
        """

        factory_index: SignalListItemFactory = SignalListItemFactory()
        factory_dialogue: SignalListItemFactory = SignalListItemFactory()
        factory_start_time: SignalListItemFactory = SignalListItemFactory()
        factory_end_time: SignalListItemFactory = SignalListItemFactory()
        factory_has_video: SignalListItemFactory = SignalListItemFactory()
        factory_has_audio: SignalListItemFactory = SignalListItemFactory()
        factory_has_image: SignalListItemFactory = SignalListItemFactory()
        column_index: ColumnViewColumn = ColumnViewColumn(title="Index", factory=factory_index)
        column_dialogue: ColumnViewColumn = ColumnViewColumn(title="Dialogue", factory=factory_dialogue)
        column_start_time: ColumnViewColumn = ColumnViewColumn(title="Start", factory=factory_start_time)
        column_end_time: ColumnViewColumn = ColumnViewColumn(title="End", factory=factory_end_time)
        column_has_video: ColumnViewColumn = ColumnViewColumn(title="Video", factory=factory_has_video)
        column_has_audio: ColumnViewColumn = ColumnViewColumn(title="Audio", factory=factory_has_audio)
        column_has_image: ColumnViewColumn = ColumnViewColumn(title="Image", factory=factory_has_image)

        column_dialogue.set_fixed_width(int(DISPLAY_WIDTH * 0.5))
        factory_index.connect("setup", self._factory_index_setup)
        factory_index.connect("bind", self._factory_index_bind)
        factory_dialogue.connect("setup", self._factory_dialogue_setup)
        factory_dialogue.connect("bind", self._factory_dialogue_bind)
        factory_start_time.connect("setup", self._factory_start_time_setup)
        factory_start_time.connect("bind", self._factory_start_time_bind)
        factory_end_time.connect("setup", self._factory_end_time_setup)
        factory_end_time.connect("bind", self._factory_end_time_bind)
        factory_has_video.connect("setup", self._factory_has_video_setup)
        factory_has_video.connect("bind", self._factory_has_video_bind)
        factory_has_audio.connect("setup", self._factory_has_audio_setup)
        factory_has_audio.connect("bind", self._factory_has_audio_bind)
        factory_has_image.connect("setup", self._factory_has_image_setup)
        factory_has_image.connect("bind", self._factory_has_image_bind)
        self._dialogues_columnview.append_column(column_index)
        self._dialogues_columnview.append_column(column_dialogue)
        self._dialogues_columnview.append_column(column_start_time)
        self._dialogues_columnview.append_column(column_end_time)
        self._dialogues_columnview.append_column(column_has_video)
        self._dialogues_columnview.append_column(column_has_audio)
        self._dialogues_columnview.append_column(column_has_image)


    def _factory_index_setup(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        list_item.set_child(Label())


    def _factory_index_bind(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        index_label: Label = cast(Label, list_item.get_child())
        row: DialogueInfo | None = cast(DialogueInfo | None, list_item.get_item())

        if not row: return

        index_label.set_label(row[DialogueInfoIndex.DIALOGUE_INDEX])


    def _factory_dialogue_setup(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        list_item.set_child(Label(use_markup=True))


    def  _factory_dialogue_bind(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        dialogue_label: Label = cast(Label, list_item.get_child())
        row: DialogueInfo | None = cast(DialogueInfo | None, list_item.get_item())

        if not row: return

        row.bind_property("dialogue", dialogue_label, "label", BindingFlags.SYNC_CREATE)
        dialogue_label.set_markup(row[DialogueInfoIndex.DIALOGUE])


    def _handle_time_field_changes(
        self,
        entry: Entry,
        list_item: ListItem,
        index: Literal[
            DialogueInfoIndex.START_TIMESTAMP,
            DialogueInfoIndex.END_TIMESTAMP
        ]
    ) -> None:
        text: str = entry.get_text()
        result: Match[str] | None = REGEX_TIMESTAMP_PATTERN.match(text)
        row: DialogueInfo | None = cast(DialogueInfo | None, list_item.get_item())

        if not row: return

        time: str = row[index]

        if not result:
            entry.set_text(time)

            return

        result_string: str = result.group().replace(",", ".")

        if result_string == time: return

        row[index] = result_string


    def _on_focus_change(
        self,
        entry: Entry,
        _: ParamSpec,
        list_item: ListItem,
        index: Literal[
            DialogueInfoIndex.START_TIMESTAMP,
            DialogueInfoIndex.END_TIMESTAMP
        ]
    ) -> None:
        self._handle_time_field_changes(entry, list_item, index)


    def _factory_start_time_setup(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        start_time_entry: Entry = Entry()

        start_time_entry.connect(
            "notify::has-focus",
            self._on_focus_change,
            list_item,
            DialogueInfoIndex.START_TIMESTAMP
        )
        list_item.set_child(start_time_entry)


    def _factory_start_time_bind(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        start_time_entry: Entry = cast(Entry, list_item.get_child())
        row: DialogueInfo | None = cast(DialogueInfo | None, list_item.get_item())

        if not row: return

        row.bind_property("start_time", start_time_entry, "text", BindingFlags.SYNC_CREATE)
        start_time_entry.set_text(row[DialogueInfoIndex.START_TIMESTAMP])


    def _factory_end_time_setup(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        end_time_entry: Entry = Entry()

        end_time_entry.connect(
            "notify::has-focus",
            self._on_focus_change,
            list_item,
            DialogueInfoIndex.END_TIMESTAMP
        )
        list_item.set_child(end_time_entry)


    def _factory_end_time_bind(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        end_time_entry: Entry = cast(Entry, list_item.get_child())
        row: DialogueInfo | None = cast(DialogueInfo | None, list_item.get_item())

        if not row: return

        row.bind_property("end_time", end_time_entry, "text", BindingFlags.SYNC_CREATE)
        end_time_entry.set_text(row[DialogueInfoIndex.END_TIMESTAMP])


    def _on_has_video_toggled(
        self,
        check_button: CheckButtonWrapper,
        list_item: ListItem
    ) -> None:
        row: DialogueInfo | None = cast(DialogueInfo | None, list_item.get_item())

        if not row: return

        is_active: bool = check_button.get_active()
        row.has_video = is_active

        if not is_active:
            self._number_medias_toggled -= 1
            return

        if row.has_audio:
            row.has_audio = False

        if row.has_image:
            row.has_image = False

        self._number_medias_toggled += 1


    def _on_has_audio_toggled(
        self,
        check_button: CheckButtonWrapper,
        list_item: ListItem
    ) -> None:
        row: DialogueInfo | None = cast(DialogueInfo | None, list_item.get_item())

        if not row: return

        is_active: bool = check_button.get_active()

        row.has_audio = is_active

        if not is_active:
            self._number_medias_toggled -= 1
            return

        if row.has_video:
            row.has_video = False

        self._number_medias_toggled += 1


    def _on_has_image_toggled(
        self,
        check_button: CheckButtonWrapper,
        list_item: ListItem
    ) -> None:
        row: DialogueInfo | None = cast(DialogueInfo | None, list_item.get_item())

        if not row: return

        is_active: bool = check_button.get_active()

        row.has_image = is_active

        if not is_active:
            self._number_medias_toggled -= 1
            return

        if row.has_video:
            row.has_video = False

        self._number_medias_toggled += 1


    def _factory_has_video_setup(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        video_check_button: CheckButtonWrapper = CheckButtonWrapper(halign=Align.CENTER, can_focus=False)

        video_check_button.connect("toggled", self._on_has_video_toggled, list_item)
        list_item.set_child(video_check_button)


    def _factory_has_video_bind(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        video_check_button: CheckButtonWrapper = cast(CheckButtonWrapper, list_item.get_child())
        row: DialogueInfo | None = cast(DialogueInfo | None, list_item.get_item())

        if not row: return

        if video_check_button.binding:
            video_check_button.binding.unbind()

        video_check_button.set_active(row.has_video)

        video_check_button.binding = row.bind_property(
            "has_video", video_check_button, "active",
            BindingFlags.BIDIRECTIONAL | BindingFlags.SYNC_CREATE
        )


    def _factory_has_audio_setup(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        audios_check_button: CheckButtonWrapper = CheckButtonWrapper(halign=Align.CENTER)

        audios_check_button.connect("toggled", self._on_has_audio_toggled, list_item)
        list_item.set_child(audios_check_button)


    def _factory_has_audio_bind(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        audio_check_button: CheckButtonWrapper = cast(CheckButtonWrapper, list_item.get_child())

        row: DialogueInfo | None = cast(DialogueInfo | None, list_item.get_item())

        if not row: return

        if audio_check_button.binding:
            audio_check_button.binding.unbind()

        audio_check_button.set_active(row.has_audio)

        audio_check_button.binding = row.bind_property(
            "has_audio", audio_check_button, "active",
            BindingFlags.BIDIRECTIONAL | BindingFlags.SYNC_CREATE
        )


    def _factory_has_image_setup(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        image_check_button: CheckButtonWrapper = CheckButtonWrapper(halign=Align.CENTER)

        image_check_button.connect("toggled", self._on_has_image_toggled, list_item)
        list_item.set_child(image_check_button)


    def _factory_has_image_bind(
        self,
        _: SignalListItemFactory,
        list_item: ListItem
    ) -> None:
        image_check_button: CheckButtonWrapper = cast(CheckButtonWrapper, list_item.get_child())

        row: DialogueInfo | None = cast(DialogueInfo | None, list_item.get_item())

        if not row: return

        if image_check_button.binding:
            image_check_button.binding.unbind()

        image_check_button.set_active(row.has_image)

        image_check_button.binding = row.bind_property(
            "has_image", image_check_button, "active",
            BindingFlags.BIDIRECTIONAL | BindingFlags.SYNC_CREATE
        )


    def _setup_front_field(self, box: Box) -> None:
        """
        _setup_front_field

        Sets the front field and its text buffer.

        :param box: Box container where the field will be added.
        :return:
        """

        text_view: TextView = TextView(hexpand=True, vexpand=True)
        self._front_field_text_buffer = text_view.get_buffer()
        label: Label = Label(label="<i><b>Front:</b></i>", halign=Align.START, use_markup=True)
        scrolled_window: ScrolledWindow = ScrolledWindow()
        self._front_field_text_buffer_handler_id: int = self._front_field_text_buffer.connect(
            "changed",
            self._on_front_field_text_buffer_changed
        )

        set_widget_margin(label, DISPLAY_WIDTH * 0.002)
        scrolled_window.set_child(text_view)
        box.append(label)
        box.append(scrolled_window)


    def _disable_front_field_text_buffer_event_listening(self) -> None:
        """
        _disalbe_front_field_text_buffer_event_listening

        Enables event listening again for the front field text buffer.

        :return:
        """

        self._front_field_text_buffer.handler_block(self._front_field_text_buffer_handler_id)


    def _enable_front_field_text_buffer_event_listening(self) -> None:
        """
        _enable_front_field_text_buffer_event_listening

        Enables event listening again for the front field text buffer.

        :return:
        """

        self._front_field_text_buffer.handler_unblock(self._front_field_text_buffer_handler_id)


    def _setup_back_field(self, box: Box) -> None:
        """
        _setup_back_field

        Sets the back field and its text buffer.

        :param box: Box container where the field will be added.
        :return:
        """

        text_view: TextView = TextView(hexpand=True, vexpand=True)
        self._back_field_text_buffer = text_view.get_buffer()
        label: Label = Label(label="<i><b>Back:</b></i>", halign=Align.START, use_markup=True)
        scrolled_window: ScrolledWindow = ScrolledWindow()
        self._back_field_text_buffer_handler_id = self._back_field_text_buffer.connect(
            "changed",
            self._on_back_field_text_buffer_changed
        )

        set_widget_margin(label, DISPLAY_WIDTH * 0.002)
        scrolled_window.set_child(text_view)
        box.append(label)
        box.append(scrolled_window)


    def _disable_back_field_text_buffer_event_listening(self) -> None:
        """
        _disalbe_back_field_text_buffer_event_listening

        Enables event listening again for the back field text buffer.

        :return:
        """

        self._back_field_text_buffer.handler_block(self._back_field_text_buffer_handler_id)


    def _enable_back_field_text_buffer_event_listening(self) -> None:
        """
        _enable_back_field_text_buffer_event_listening

        Enables event listening again for the back field text buffer.

        :return:
        """

        self._back_field_text_buffer.handler_unblock(self._back_field_text_buffer_handler_id)


    def _on_front_field_text_buffer_changed(self, text_buffer: TextBuffer) -> None:
        """
        _on_front_field_text_buffer_changed

        Handles the "changed" signal emmited by the front field's TextBuffer object.

        :param text_buffer: TextBuffer object which emitted the signal.
        :return:
        """

        row: DialogueInfo | None = cast(DialogueInfo | None, self._selected_row.get_selected_item())

        if not row: return

        row[DialogueInfoIndex.DIALOGUE] = get_tagged_text_from_text_buffer(text_buffer)


    def _on_back_field_text_buffer_changed(self, text_buffer: TextBuffer) -> None:
        """
        _on_back_field_text_buffer_changed

        Handles the "changed" signal emmited by the back field's TextBuffer object.

        :param text_buffer: TextBuffer object which emitted the signal.
        :return:
        """

        row: DialogueInfo | None = cast(DialogueInfo | None, self._selected_row.get_selected_item())

        if not row: return

        index: int = row.get_index()
        back: DialogueInfo = cast(DialogueInfo, self._back_field_list_store[index])
        back[DialogueInfoIndex.DIALOGUE] = get_tagged_text_from_text_buffer(text_buffer)


    def _setup_search_entry(self) -> None:
        """
        _setup_search_entry

        Setup the search entry to lookup for specific dialogues.

        :return:
        """

        self._search_entry = SearchEntry(halign=Align.END)
        custom_filter: CustomFilter = CustomFilter.new(self._dialogues_filter_func, None)
        filter_list_model: FilterListModel = FilterListModel(
            model=self._front_field_list_store.get_list_store(),
            filter=custom_filter
        )

        set_widget_margin(self._search_entry, DISPLAY_WIDTH * 0.002)
        self._selected_row.set_model(filter_list_model)
        self._search_entry.connect("search-changed", self._on_search_changed, filter_list_model)
        self._main_grid.attach(self._search_entry, 0, 0, 1, 1)


    def _dialogues_filter_func(self, row: DialogueInfo, *_: object) -> bool:
        """
        _dialogues_filter_func

        Function called to determine if the row should be matched.

        :param row: DialogueInfo Gtk.GObject derived object.
        :param user_data: Arguments.
        :return: True if the filter matches the search term in the row.
        """

        search_term: str = self._search_entry.get_text().lower()

        if not search_term: return True

        return search_term in row[DialogueInfoIndex.DIALOGUE].lower()


    def _on_search_changed(
        self,
        search_entry: SearchEntry,
        filter_list_model: FilterListModel
    ) -> None:
        """
        _on_search_changed

        Handles the search-changed signal.

        :param search_entry: SearchEntry widget which emmited the signal.
        :param filter_list_model: List model filter.
        :return:
        """

        custom_filter: CustomFilter = cast(CustomFilter, filter_list_model.get_filter())

        self._row_selection.block_selection_updates()
        custom_filter.changed(FilterChange.DIFFERENT)

        n_items: int = filter_list_model.get_n_items()

        if n_items == 0:
            self._force_emit_selection_changed()
            return

        search_term: str = search_entry.get_text()

        if not search_term:
            self._row_selection.unblock_selection_updates()
            self._selected_row.set_selected(INVALID_LIST_POSITION)
            self._selected_row.set_selected(self._row_selection.index)
            self._dialogues_columnview.scroll_to(self._row_selection.index, None, ListScrollFlags.NONE, None)
            return

        self._force_emit_selection_changed(position=self._selected_row.get_selected(), n_items=1)


    def _setup_toolbar(self, toolbar_box: Box) -> None:
        """
        _setup_toolbar

        Setup the toolbar widgets.

        :param toolbar_box: Box container to arrenge the buttons.
        :return:
        """

        separator_1: Separator = Separator()
        separator_2: Separator = Separator()
        separator_3: Separator = Separator()
        separator_4: Separator = Separator()

        margin: float = DISPLAY_WIDTH * 0.002
        set_widget_margin(separator_1, start=margin, end=margin)
        set_widget_margin(separator_2, start=margin, end=margin)
        set_widget_margin(separator_3, start=margin, end=margin)
        set_widget_margin(separator_4, start=margin, end=margin)

        self._setup_toolbar_color_button(toolbar_box)
        toolbar_box.append(separator_1)
        self._setup_toolbar_underline_button(toolbar_box)
        toolbar_box.append(separator_2)
        self._setup_toolbar_bold_button(toolbar_box)
        toolbar_box.append(separator_3)
        self._setup_toolbar_italic_button(toolbar_box)
        toolbar_box.append(separator_4)
        self._setup_toolbar_remove_all_tags_button(toolbar_box)


    def _setup_toolbar_color_button(self, toolbar_box: Box) -> None:
        """
        _setup_toolbar_color_button

        Setup the toolbar color button.

        :param toolbar_box: Box container to arrenge the buttons.
        :return:
        """

        box: Box = Box()
        color_dialog: ColorDialog = ColorDialog(with_alpha=False, modal=True)
        color_dialog.set_title
        apply_color_button: Button = Button()
        color_button: Button = Button()
        palette_gicon: Icon = Icon.new_for_string(
            path.join(ICONS_SYMBOLIC_DIRECTORY,
            "palette-symbolic.svg")
        )
        apply_color_gicon: Icon = Icon.new_for_string(
            path.join(ICONS_SYMBOLIC_DIRECTORY,
            "apply-color-symbolic.svg")
        )
        palette_image: Image = Image.new_from_gicon(palette_gicon)
        apply_color_image: Image = Image.new_from_gicon(apply_color_gicon)
        apply_color_image_style_context: StyleContext = apply_color_image.get_style_context()
        apply_color_image_css_manager: CssManager = CssManager(
            apply_color_image_style_context,
            STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        apply_color_image_css_class_name: str = "apply-color-image"
        apply_color_image_css_manager[f".{apply_color_image_css_class_name}"] = (
            f"{{ color: {self._currently_selected_color.hex_8bits_channel_string}; }}"
        )

        color_button.set_tooltip_text("Selects a color to apply to the foreground of text.")
        apply_color_button.set_tooltip_text("Apply the selected color to the text.")
        apply_color_image.add_css_class(apply_color_image_css_class_name)
        color_button.set_child(palette_image)
        apply_color_button.set_child(apply_color_image)
        box.append(apply_color_button)
        box.append(color_button)
        color_button.connect(
            "clicked",
            self._on_color_button_clicked,
            color_dialog,
            apply_color_button,
            apply_color_image_css_manager,
            apply_color_image_css_class_name
        )
        apply_color_button.connect("clicked", self._on_apply_color_button_clicked)
        toolbar_box.append(box)


    def _on_color_button_clicked(
        self,
        _: Button,
        color_dialog: ColorDialog,
        apply_color_button: Button,
        css_manager: CssManager,
        css_class_name: str
    ) -> None:
        """
        _on_color_button_clicked

        Handles the clicked event for the color button.

        :param color_dialog: ColorDialog which should be opened after the button click.
        :param apply_color_button: Button that emitted the event.
        :param css_manager: CssManager class object to manage widget's CSS properties.
        :param css_class_name: Widget's CSS class name that should be managed by the CssManager.
        :return:
        """

        color_dialog.choose_rgba(
            self,
            self._currently_selected_color,
            None,
            self._on_color_selected,
            apply_color_button,
            css_manager,
            css_class_name
        )


    def _on_color_selected(
        self,
        color_dialog: ColorDialog,
        result: AsyncResult,
        apply_color_button: Button,
        css_manager: CssManager,
        css_class_name: str
    ) -> None:
        """
        _on_color_selected

        Handles the selection of color from ColorDialog.

        :param color_dialog: ColorDialog which the color selection was completed.
        :param result: Asynchronous function result.
        :param apply_color_button: Button that should receive the selected color.
        :param css_manager: CssManager class object to manage widget's CSS properties.
        :param css_class_name: Widget's CSS class name that should be managed by the CssManager.
        :return:
        """

        gdk_rgba: GdkRGBA | None = handle_exception_if_any("", False, color_dialog.choose_rgba_finish, result)
        rgba: RGBA | None = RGBA.create_from(gdk_rgba) if gdk_rgba else None

        if not rgba: return

        self._currently_selected_color = rgba
        widget: Widget | None = apply_color_button.get_child()

        if not widget: return

        css_manager[f".{css_class_name}"] = f"{{ color: {rgba.hex_8bits_channel_string}; }}"


    def _on_apply_color_button_clicked(self, _: Button) -> None:
        """
        _on_apply_color_button_clicked

        Handles the clicked event for the apply_color_button.

        :param apply_color_button: Button that was clicked.
        :return:
        """

        row: DialogueInfo | None = cast(DialogueInfo | None, self._selected_row.get_selected_item())

        if not row: return

        tag_name: str = f"foreground={self._currently_selected_color.hex_16bits_channel_string}"
        start_selection_text_iter: TextIter
        end_selection_text_iter: TextIter
        front_selection_bounds: SelectionBounds
        back_selection_bounds: SelectionBounds
        (front_selection_bounds, back_selection_bounds) = self._get_selection_bounds()

        if front_selection_bounds:
            (start_selection_text_iter, end_selection_text_iter) = front_selection_bounds
            front_field_text_tag_table: TextTagTable = self._front_field_text_buffer.get_tag_table()
            self._remove_tags_from_selection(
                self._front_field_text_buffer,
                front_selection_bounds,
                front_field_text_tag_table,
                "foreground-set"
            )

            tag: TextTag | None = front_field_text_tag_table.lookup(tag_name)

            if not tag:
                self._front_field_text_buffer.create_tag(
                    tag_name,
                    foreground_rgba=self._currently_selected_color
                )

            self._front_field_text_buffer.apply_tag_by_name(
                tag_name,
                start_selection_text_iter,
                end_selection_text_iter
            )

            row[DialogueInfoIndex.DIALOGUE] = get_tagged_text_from_text_buffer(self._front_field_text_buffer)

            return

        if not back_selection_bounds: return

        back_field_text_tag_table: TextTagTable = self._back_field_text_buffer.get_tag_table()

        self._remove_tags_from_selection(
            self._back_field_text_buffer,
            back_selection_bounds,
            back_field_text_tag_table,
            "foreground-set"
        )

        (start_selection_text_iter, end_selection_text_iter) = back_selection_bounds
        tag: TextTag | None = back_field_text_tag_table.lookup(tag_name)

        if not tag:
            self._back_field_text_buffer.create_tag(
                tag_name,
                foreground_rgba=self._currently_selected_color
            )

        self._back_field_text_buffer.apply_tag_by_name(
            tag_name,
            start_selection_text_iter,
            end_selection_text_iter
        )

        back: DialogueInfo = cast(DialogueInfo, self._back_field_list_store[row.get_index()])
        back[DialogueInfoIndex.DIALOGUE] = get_tagged_text_from_text_buffer(self._back_field_text_buffer)


    def _setup_toolbar_underline_button(self, toolbar: Box) -> None:
        """
        _setup_toolbar_underline_button

        Setup the toolbar underline button.

        :param toolbar_box: Box container to arrenge the buttons.
        :return:
        """

        underline_button: Button = Button()
        gicon: Icon = Icon.new_for_string(
            path.join(
                ICONS_SYMBOLIC_DIRECTORY,
                "format-text-underline-symbolic.svg"
            )
        )
        image: Image = Image.new_from_gicon(gicon)
        text_tag_underline_front: TextTag = self._front_field_text_buffer.create_tag(
            "u",
            underline=Underline.SINGLE
        )
        text_tag_underline_back: TextTag = self._back_field_text_buffer.create_tag(
            "u",
            underline=Underline.SINGLE
        )

        underline_button.set_tooltip_text("Apply underline tag to text.")
        underline_button.connect(
            "clicked",
            self._on_apply_format_text_tag,
            text_tag_underline_front,
            text_tag_underline_back
        )
        underline_button.set_child(image)
        toolbar.append(underline_button)


    def _setup_toolbar_bold_button(self, toolbar: Box) -> None:
        """
        _setup_toolbar_bold_button

        Setup the toolbar bold button.

        :param toolbar_box: Box container to arrenge the buttons.
        :return:
        """

        bold_button: Button = Button()
        gicon: Icon = Icon.new_for_string(
            path.join(
                ICONS_SYMBOLIC_DIRECTORY,
                "format-text-bold-symbolic.svg"
            )
        )
        image: Image = Image.new_from_gicon(gicon)
        text_tag_bold_front: TextTag = self._front_field_text_buffer.create_tag(
            "b",
            weight=Weight.BOLD
        )
        text_tag_bold_back: TextTag = self._back_field_text_buffer.create_tag(
            "b",
            weight=Weight.BOLD
        )

        bold_button.set_tooltip_text("Apply bold tag to text.")
        bold_button.connect(
            "clicked",
            self._on_apply_format_text_tag,
            text_tag_bold_front,
            text_tag_bold_back
        )
        bold_button.set_child(image)
        toolbar.append(bold_button)


    def _setup_toolbar_italic_button(self, toolbar: Box) -> None:
        """
        _setup_toolbar_italic_button

        Setup the toolbar italic button.

        :param toolbar_box: Box container to arrenge the buttons.
        :return:
        """

        italic_button: Button = Button()
        gicon: Icon = Icon.new_for_string(
            path.join(
                ICONS_SYMBOLIC_DIRECTORY,
                "format-text-italic-symbolic.svg"
            )
        )
        image: Image = Image.new_from_gicon(gicon)
        text_tag_italic_front: TextTag = self._front_field_text_buffer.create_tag(
            "i",
            style=Style.ITALIC
        )
        text_tag_italic_back: TextTag = self._back_field_text_buffer.create_tag(
            "i",
            style=Style.ITALIC
        )

        italic_button.set_tooltip_text("Apply italic tag to text.")
        italic_button.connect(
            "clicked",
            self._on_apply_format_text_tag,
            text_tag_italic_front,
            text_tag_italic_back
        )
        italic_button.set_child(image)
        toolbar.append(italic_button)


    def _setup_toolbar_remove_all_tags_button(self, toolbar: Box) -> None:
        """
        _setup_toolbar_remove_all_tags_button

        Setup the toolbar italic button.

        :param toolbar_box: Box container to arrenge the buttons.
        :return:
        """

        remove_all_tags_button: Button = Button()
        gicon: Icon = Icon.new_for_string(
            path.join(
                ICONS_SYMBOLIC_DIRECTORY,
                "clear-edit-symbolic.svg"
            )
        )
        image: Image = Image.new_from_gicon(gicon)

        remove_all_tags_button.set_tooltip_text("Removes all tags applied to the selected text.")
        remove_all_tags_button.connect("clicked", self._remove_all_tags_from_selection)
        remove_all_tags_button.set_child(image)
        toolbar.append(remove_all_tags_button)


    def _remove_all_tags_from_selection(self, _: Button) -> None:
        """
        _remove_all_tags_from_selection

        Removes all tags from the selection.

        :param button: Button that emitted the signal.
        :return:
        """

        row: DialogueInfo | None = cast(DialogueInfo | None, self._selected_row.get_selected_item())

        if not row: return

        start_selection_text_iter: TextIter
        end_selection_text_iter: TextIter
        front_selection_bounds: SelectionBounds
        back_selection_bounds: SelectionBounds
        (front_selection_bounds, back_selection_bounds) = self._get_selection_bounds()

        if front_selection_bounds:
            (start_selection_text_iter, end_selection_text_iter) = front_selection_bounds

            self._front_field_text_buffer.remove_all_tags(
                start_selection_text_iter,
                end_selection_text_iter
            )

            row[DialogueInfoIndex.DIALOGUE] = get_tagged_text_from_text_buffer(self._front_field_text_buffer)

            return

        if not back_selection_bounds: return

        (start_selection_text_iter, end_selection_text_iter) = back_selection_bounds

        self._front_field_text_buffer.remove_all_tags(
            start_selection_text_iter,
            end_selection_text_iter
        )

        back: DialogueInfo = cast(DialogueInfo, self._back_field_list_store[row.get_index()])
        back[DialogueInfoIndex.DIALOGUE] = get_tagged_text_from_text_buffer(self._back_field_text_buffer)


    def _on_apply_format_text_tag(
        self,
        _: Button,
        front_field_text_tag: TextTag,
        back_field_text_tag: TextTag
    ) -> None:
        """
        _on_apply_format_text_tag

        :param button: Button that emitted the event.
        :param front_field_text_tag:
        :param back_field_text_tag:
        :return:
        """

        row: DialogueInfo | None = cast(DialogueInfo | None, self._selected_row.get_selected_item())

        if not row: return

        start_selection_text_iter: TextIter
        end_selection_text_iter: TextIter
        front_selection_bounds: SelectionBounds
        back_selection_bounds: SelectionBounds
        (front_selection_bounds, back_selection_bounds) = self._get_selection_bounds()

        if front_selection_bounds:
            (start_selection_text_iter, end_selection_text_iter) = front_selection_bounds
            self._front_field_text_buffer.apply_tag(
                front_field_text_tag,
                start_selection_text_iter,
                end_selection_text_iter
            )

            row[DialogueInfoIndex.DIALOGUE] = get_tagged_text_from_text_buffer(self._front_field_text_buffer)

            return

        if not back_selection_bounds: return

        (start_selection_text_iter, end_selection_text_iter) = back_selection_bounds

        self._back_field_text_buffer.apply_tag(
            back_field_text_tag,
            start_selection_text_iter,
            end_selection_text_iter
        )

        back: DialogueInfo = cast(DialogueInfo, self._back_field_list_store[row.get_index()])
        back[DialogueInfoIndex.DIALOGUE] = get_tagged_text_from_text_buffer(self._back_field_text_buffer)


    def _get_selection_bounds(self) -> tuple[SelectionBounds, SelectionBounds]:
        """
        _get_selection_bounds

        Gets the selection bounds (start and end TextIter) if any field has a selection.

        :return: A tuple with the start and end iter
                 of the selection of both (front and back) TextBuffer.
        """

        return (self._front_field_text_buffer.get_selection_bounds(),
                self._back_field_text_buffer.get_selection_bounds()
        )


    def _remove_tags_from_selection(
        self,
        text_buffer: TextBuffer,
        selection_bounds: SelectionBounds,
        text_tag_table: TextTagTable,
        property_name: str
    ) -> None:
        """
        _remove_tags_from_selection

        Remove the tag with property_name from the selection of the TextBuffer.

        :param text_buffer: TextBuffer from which the tags with property_name should be removed.
        :param selection_bounds: A tuple with the start and end TextIter repreemmiteding the selection.
        :param text_tag_table: Text buffer's tag table.
        :param property_name: The property tag name that should be removed from the text buffer selection.
        :return:
        """

        if not selection_bounds: return

        text_tag_table.foreach(
            lambda tag: \
            text_buffer.remove_tag(tag, selection_bounds[0], selection_bounds[1]) \
            if tag.get_property(property_name) \
            else None
        )


    def _setup_select_all_medias_check_buttons(self) -> None:
        """
        _setup_select_all_medias_check_buttons

        Setup check buttons for selecting all medias.

        :return:
        """

        grid: Grid = Grid(halign=Align.END)
        videos_box: Box = Box(orientation=Orientation.VERTICAL)
        audios_box: Box = Box(orientation=Orientation.VERTICAL)
        images_box: Box = Box(orientation=Orientation.VERTICAL)
        main_frame: Frame = Frame(halign=Align.END, child=grid)
        videos_frame: Frame = Frame(child=videos_box)
        audios_frame: Frame = Frame(child=audios_box)
        images_frame: Frame = Frame(child=images_box)
        videos_label: Label = Label(label="Videos", halign=Align.CENTER)
        audios_label: Label = Label(label="Audios", halign=Align.CENTER)
        images_label: Label = Label(label="Images", halign=Align.CENTER)
        all_videos_check_button: CheckButtonWrapper = CheckButtonWrapper(halign=Align.CENTER)
        all_audios_check_button: CheckButtonWrapper = CheckButtonWrapper(halign=Align.CENTER)
        all_images_check_button: CheckButtonWrapper = CheckButtonWrapper(halign=Align.CENTER)

        set_widget_margin(videos_frame, DISPLAY_WIDTH * 0.005)
        set_widget_margin(audios_frame, DISPLAY_WIDTH * 0.005)
        set_widget_margin(images_frame, DISPLAY_WIDTH * 0.005)
        all_videos_check_button.set_tooltip_text("Select all videos.")
        all_audios_check_button.set_tooltip_text("Select all audios.")
        all_images_check_button.set_tooltip_text("Select all images.")
        all_videos_check_button.connect(
            "toggled",
            self._on_select_all_videos_toggled,
            all_audios_check_button,
            all_images_check_button
        )
        all_audios_check_button.connect(
            "toggled",
            self._on_select_all_audios_toggled,
            all_videos_check_button
        )
        all_images_check_button.connect(
            "toggled",
            self._on_select_all_images_toggled,
            all_videos_check_button
        )
        videos_box.append(videos_label)
        videos_box.append(all_videos_check_button)
        audios_box.append(audios_label)
        audios_box.append(all_audios_check_button)
        images_box.append(images_label)
        images_box.append(all_images_check_button)
        grid.attach(videos_frame, 0, 0, 1, 1)
        grid.attach(audios_frame, 1, 0, 1, 1)
        grid.attach(images_frame, 2, 0, 1, 1)
        self._main_grid.attach(main_frame, 0, 2, 1, 1)


    def _on_select_all_videos_toggled(
        self,
        all_videos_check_button: CheckButtonWrapper,
        all_audios_check_button: CheckButtonWrapper,
        all_images_check_button: CheckButtonWrapper
    ) -> None:
        """
        _on_select_all_videos_toggled

        Handles the toggled event emitted by all_videos_check_button.

        :param all_videos_check_button: CheckButton that emitted the event.
        :param all_audios_check_button: CheckButton responsible for the toggle of audio medias.
        :param all_images_check_button: CheckButton responsible for
                                           the toggle of images medias.
        :return:
        """

        is_toggled: bool = all_videos_check_button.get_active()

        for dialogue_info in self._front_field_list_store:
            dialogue_info.has_video = is_toggled

        if is_toggled:
            all_audios_check_button.set_active(False)
            all_images_check_button.set_active(False)


    def _on_select_all_audios_toggled(
        self,
        all_audios_check_button: CheckButtonWrapper,
        all_videos_check_button: CheckButtonWrapper
    ) -> None:
        """
        _on_select_all_audios_toggled

        Handles the toggled event emitted by all_audios_check_button.

        :param all_audios_check_button: CheckButton that emitted the event.
        :param all_videos_check_button: CheckButton responsible for the toggle of video medias.
        :return:
        """

        is_toggled: bool = all_audios_check_button.get_active()

        for dialogue_info in self._front_field_list_store:
            dialogue_info.has_audio = is_toggled

        if is_toggled:
            all_videos_check_button.set_active(False)


    def _on_select_all_images_toggled(
        self,
        all_images_check_button: CheckButtonWrapper,
        all_videos_check_button: CheckButtonWrapper
        ) -> None:
        """
        _on_select_all_images_toggled

        Handles the toggled event emitted by all_images_check_button.

        :param all_images_check_button: CheckButton that emitted the event.
        :param all_videos_check_button: CheckButton responsible for the toggle of video medias.
        :return:
        """

        is_toggled: bool = all_images_check_button.get_active()

        for dialogue_info in self._front_field_list_store:
            dialogue_info.has_image = is_toggled

        if is_toggled:
            all_videos_check_button.set_active(False)


    def _setup_cancel_button(self, buttons_box: Box) -> None:
        """
        _setup_cancel_button

        Setup the cancel button for the cards editor window.

        :param buttons_box: Box container to hold the cancel button.
        :return:
        """

        self._cancel_button: Button = Button(label="Cancel")

        set_widget_margin(
            self._cancel_button,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.1,
            DISPLAY_WIDTH * 0.005
        )
        self._cancel_button.connect("clicked", self._on_cancel_button_clicked)
        buttons_box.append(self._cancel_button)


    def _on_cancel_button_clicked(self, _: Button) -> None:
        """
        _on_cancel_clicked

        Handles the clicked signal emitted by the cancel button.

        :param button: Button that emmited the signal.
        :return:
        """

        if self._cards_editor_state.is_state(CardsEditorStates.RUNNING):
            self._cards_editor_state.set_state(CardsEditorStates.CANCELLED)
            timeout_add(300, self._set_cancel_button_sensitive)

            return

        self.close()


    def _set_cancel_button_sensitive(self) -> bool:
        """
        _set_cancel_button_sensitive

        Callback to watch for the conditions to set the cancel_button sensitive.

        :return:
        """

        if self._are_all_futures_done():
            self._cancel_button.set_sensitive(True)
            self._progress_bar.set_text("Cancelled.")
            self._cards_editor_state.set_state(CardsEditorStates.NORMAL)

            return False

        self._cancel_button.set_sensitive(False)
        self._progress_bar.set_text("Cancelling, please wait.")

        return True


    def _setup_generate_button(self, buttons_box: Box) -> None:
        """
        _setup_generate_button

        Setup the generate button for the cards editor window.

        :param buttons_box: Box container to hold the generate button.
        :return:
        """

        self._generate_button: Button = Button(label="Generate", sensitive=False)

        set_widget_margin(
            self._generate_button,
            DISPLAY_WIDTH * 0.1,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.005
        )
        self._generate_button.connect("clicked", self._on_generate_button_clicked)
        buttons_box.append(self._generate_button)
        timeout_add(150, self._set_generate_button_sensitive)


    def _set_generate_button_sensitive(self) -> bool:
        """
        _set_generate_button_sensitive

        Callback to watch for the conditions to set the generate_button sensitive.

        :return: A boolean value to tell if this callback should still be called.
        """

        if (not self._number_medias_toggled > 0
            or not self._are_all_futures_done()
            or (self._progress_bar.get_fraction() > 0
            and self._progress_bar.get_fraction() < 1)):
            self._generate_button.set_sensitive(False)
        else:
            self._generate_button.set_sensitive(True)

        return True


    def _are_all_futures_done(self) -> bool:
        """
        _is_all_futures_done

        Tells whether or not all futures are done.

        :return: True if all futures are done.
        """

        return all(future.done() for future in self._futures_list)


    def _on_generate_button_clicked(self, _: Button) -> None:
        """
        _on_generate_button_clicked

        Handles the clicked event emmited by generate_button.

        :param generate_button: Button that emmited the event.
        :return:
        """

        try:
            cards_generator: CardsGenerator = CardsGenerator(
                self._collection_filepath,
                self._video_filepath,
                self._front_field_list_store,
                self._back_field_list_store,
                self._deck_name,
                self._cards_editor_state,
                self.idle_add_update_progress_bar
            )
        except Exception as e:
            warning_dialog: WarningDialog = WarningDialog(self)

            warning_dialog.set_warning_message(str(e))
            warning_dialog.show_all()

            return

        self._progress_bar.set_fraction(0)
        self._progress_bar.set_show_text(True)
        cards_generator.start()

        self._futures_list = cards_generator.get_futures_list()

        timeout_add(300, self._on_all_futures_done_empty_futures_list)


    def _on_all_futures_done(self) -> bool:
        """
        _on_all_futures_done

        Reset the CardsEditor widgets status when all tasks are done already.

        :return: A boolean value to tell whether this callback should still be called.
        """

        if not self._are_all_futures_done(): return True

        self._cards_editor_state.set_state(CardsEditorStates.NORMAL)

        return False


    def _on_all_futures_done_empty_futures_list(self) -> bool:
        """
        _on_all_futures_done_empty_futures_list

        Callback to watch for the conditions to empty the futures_list.

        :return: A boolean value to tell whether this callback should still be called.
        """

        if not self._are_all_futures_done(): return True

        self._futures_list = []

        return False


    def _setup_progress_bar(self, buttons_box: Box) -> None:
        """
        _setup_progress_bar

        Setup the progress bar.

        :param buttons_box: Container to hold the progress bar.
        :return:
        """

        self._progress_bar = ProgressBar()

        set_widget_margin(self._progress_bar, DISPLAY_WIDTH * 0.005)
        self._progress_bar.set_fraction(0)
        buttons_box.append(self._progress_bar)


    def _update_progress_bar(self, current_completed_task: int, total_number_tasks: int) -> bool:
        """
        _update_progress_bar

        Updates the progress of progress bar.

        :param current_completed_task: Number of the current completed task.
        :param total_number_tasks: Total number of tasks to be completed.
        :return: False to remove this callback from the list of
                 event sources and to not be called again.
        """

        text: str | None = (
            None if current_completed_task < total_number_tasks
            else "Cancelled." if self._cards_editor_state.is_state(CardsEditorStates.CANCELLED)
            else "Done"
        )
        fraction: float = (
            current_completed_task / total_number_tasks
            if not self._cards_editor_state.is_state(CardsEditorStates.CANCELLED)
            else 1.0
        )

        self._progress_bar.set_fraction(fraction)
        self._progress_bar.set_text(text)
        self._progress_bar.set_show_text(True)

        return False


    def _reset_progress_bar(self) -> None:
        """
        _reset_progress_bar

        Resets the progress bar to zero progress.

        :return:
        """

        self._progress_bar.set_fraction(0)
        self._progress_bar.set_show_text(False)


    def idle_add_update_progress_bar(
        self,
        current_completed_task: int,
        total_number_tasks: int
    ) -> None:
        """
        idle_add_update_progress_bar

        :param current_completed_task: Number of the current completed task.
        :param total_number_tasks: Total number of tasks to be completed.
        :return:
        """

        idle_add(self._update_progress_bar, current_completed_task, total_number_tasks)


__all__: list[str] = ["CardsEditor"]

