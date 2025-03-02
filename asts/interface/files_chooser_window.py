from asts.custom_typing.globals import (
    GTK_VERSION, GLIB_VERSION, GIO_VERSION,
    PANGO_VERSION, GOBJECT_VERSION
)

from gi import require_version
require_version(*GIO_VERSION)
require_version(*GTK_VERSION)
require_version(*GLIB_VERSION)
require_version(*PANGO_VERSION)
require_version(*GOBJECT_VERSION)

from gi.repository.GObject import ParamSpec
from gi.repository.GLib import timeout_add, idle_add
from gi.repository.GLib import Error as GLibError
from gi.repository.Gio import AsyncResult, File, Icon
from gi.repository.Gtk import (
    Align, Application, Box, Button, DropDown, Entry,
    FileDialog, FileFilter, Frame,
    Grid, Label, Image, Orientation, StringList, StringObject, Window
)
from gi.repository.Pango import EllipsizeMode

from typing     import Any, Callable, cast, Literal
from enum       import Enum
from os         import path
from subprocess import Popen
from threading  import Thread

from asts.interface.loading_screen import LoadingScreen
from asts.interface.cards_editor import CardsEditor
from asts.custom_typing.globals  import ICONS_SYMBOLIC_DIRECTORY, DISPLAY_WIDTH, DISPLAY_HEIGHT
from asts.custom_typing.aliases import Filepath, OptionalFilepath
from asts.utils.core_utils import _print, handle_exception_if_any, NEW_LINE
from asts.utils.extra_utils import (
    create_cache_dir,
    is_file_collection, is_file_subtitles, is_file_video, cache_recently_used_files,
    get_recently_used_files, set_widget_margin, get_available_encoded_languages, write_subtitle_file
)

class _CustomFileChooser(Box):
    def __init__(self,
        title: str = "Select a File",
        label: str = "Empty",
        parent: Window | None = None,
        selection_callbacks: list[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]] = [],
        deselection_callbacks: list[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]] = []
    ) -> None:
        """
        CustomFileChooser

        A button that opens a Gtk.FileDialog window.

        :param title: Title of the FileChooserDialog window.
        :param label: Button's label.
        :param parent: The parent window where the button is placed.
        :param selection_callbacks: Callback functions to be called when a file is selected and its arguments if any.
        :param deselection_callbacks: Callback functions to be called when a file is deselected and its arguments if any.
        :return:
        """

        super().__init__(orientation=Orientation.HORIZONTAL)

        self._text_label: Label = Label(label=label, ellipsize=EllipsizeMode.END)
        self._button: Button = Button()
        self._title: str = title
        self._filepath: str = ""
        self._parent: Window | None = parent
        self._file_chooser_dialog: FileDialog
        self._selection_callbacks: list[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]] = selection_callbacks
        self._deselection_callbacks: list[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]] = deselection_callbacks
        self._button.set_child(self._text_label)
        set_widget_margin(self, DISPLAY_WIDTH * 0.005)
        self._button.set_hexpand(True)
        self._button.connect("clicked", self._on_button_clicked)
        self.append(self._button)

        self._file_chooser_dialog: FileDialog = FileDialog(
            title=self._title,
            modal=True,
        )


    def _on_button_clicked(self, _: Button) -> None:
        """
        _on_button_clicked

        :param button: Button.
        :return:
        """

        self._file_chooser_dialog.open(self._parent, None, self._on_file_dialog_response)


    def _on_file_dialog_response(self, dialog: FileDialog, result: AsyncResult) -> None:
        """
        _on_file_dialog_response

        :param dialog: FileDialog.
        :param result: AsyncResult.
        :return:
        """

        try:
            file: File | None = dialog.open_finish(result)

            if not file:
                _print("Error selecting file" + NEW_LINE, True)
                return

            filepath: str | None = file.get_path()

            if not filepath:
                _print("Error getting filepath." + NEW_LINE, True)
                return

            self.set_filename(filepath)

        except GLibError as e:
            self.unselect_all()
            _print(f"dialog.open_finish: {e}." + NEW_LINE + "Error selecting file." + NEW_LINE)


    def add_file_filter(self, file_filter: FileFilter) -> None:
        """
        add_file_filter

        Setup filters for the FileDialog.

        :param file_filter: Files filter.
        :return:
        """

        self._file_chooser_dialog.set_default_filter(file_filter)


    def get_filepath(self) -> str:
        """
        get_filepath

        :return: The filepath of the selected file if any or an empty string otherwise.
        """

        return self._filepath


    def set_filename(self, filepath: str) -> None:
        """
        set_filename

        Sets the initial file for the FileDialog.

        :param filepath: Filepath.
        :return:
        """

        file: File = File.new_for_path(filepath)
        self._filepath = filepath

        self._file_chooser_dialog.set_initial_file(file)
        self._text_label.set_label(path.basename(self._filepath))

        for callback, args, kwargs in self._selection_callbacks:
            callback(*args, *kwargs)


    def unselect_all(self) -> None:
        """
        unselect_all

        Deselects any file.

        :return:
        """

        self._filepath = ""

        self._text_label.set_label("Empty")
        self._file_chooser_dialog.set_initial_file(None)
        self.set_sensitive(True)

        for callback, args, kwargs in self._deselection_callbacks:
            callback(*args, *kwargs)


class _FileChooserButtonIndex(Enum):
    ANKI2_COLLECTION    = 0
    VIDEO               = 1
    SUBTITLE            = 2
    OPTIONAL_SUBTITLE   = 3


    def __index__(self) -> Literal[0, 1, 2, 3]:
        return self.value


class FilesChooserWindow(Window):
    def __init__(self, app: Application) -> None:
        """
        FilesChooserWindow

        A window holding FileChooserDialog buttons for selecting files needed
        to create cards

        :param app: Application.
        :return:
        """

        super().__init__(title='Asts', application=app)

        self._app: Application = app
        self._main_box: Box = Box(orientation=Orientation.VERTICAL)
        main_box_frame: Frame = Frame(child=self._main_box)
        self._main_grid: Grid = Grid()
        main_grid_frame: Frame = Frame(child=self._main_grid)
        self._dropdown_target: DropDown
        self._dropdown_optional: DropDown
        self._entry: Entry
        self._next_button: Button
        self._loading_screen: LoadingScreen = LoadingScreen(self)
        self._filechoosers_list: list[_CustomFileChooser] = self._setup_file_choosers()
        self._available_languages: dict[str, dict[str, str]] = {}

        self.set_resizable(False)
        self.set_default_size(int(DISPLAY_WIDTH * 0.85), int(DISPLAY_HEIGHT * 0.85))
        set_widget_margin(main_box_frame, DISPLAY_WIDTH * 0.005)
        set_widget_margin(main_grid_frame, DISPLAY_WIDTH * 0.005)
        set_widget_margin(self._main_box, DISPLAY_WIDTH * 0.005)
        set_widget_margin(self._main_grid, DISPLAY_WIDTH * 0.005)
        self._main_box.append(main_grid_frame)
        self._setup_labels()
        self._setup_dropdowns()
        self._setup_text_entry()
        create_cache_dir()
        self._fill_cached_file()
        self._setup_filters()
        self._setup_buttons_signals()
        self.set_child(main_box_frame)


    def _setup_labels(self) -> None:
        """
        _setup_labels

        Setup the labels for the grid.

        :return:
        """

        labels: list[Label] = [
            Label(label='collection.anki2 File (Required):'),
            Label(label='Video (Required):'),
            Label(label='Subtitle File with The Target Language (Optional):'),
            Label(label='Subtitle File with Translation (Optional):'),
            Label(label='Deck Name (Required):')
        ]

        for (i, label) in enumerate(labels):
            frame: Frame = Frame(child=label)
            label.set_halign(Align.START)
            set_widget_margin(
                frame,
                DISPLAY_WIDTH * 0.005,
                DISPLAY_WIDTH * 0.0025,
                DISPLAY_WIDTH * 0.005,
                DISPLAY_WIDTH * 0.0025
            )
            self._main_grid.attach(frame, 0, i, 1, 1)


    def _setup_file_choosers(self) -> list[_CustomFileChooser]:
        """
        _setup_file_choosers

        Set up the file choosers for the grid.

        :return: The file choosers created.
        """

        filechooser_list: list[_CustomFileChooser] = []

        for i in range(4):
            if i == _FileChooserButtonIndex.VIDEO.value:
                filechooser_list.append(
                    _CustomFileChooser(
                        parent = self,
                         # callbacks without args or kwargs
                        selection_callbacks = [
                            (self.set_available_languages_target, (), {}),
                            (self.set_available_languages_optional, (), {})
                        ],
                        deselection_callbacks = [
                            (self.reset_available_languages_target, (), {}),
                            (self.reset_available_languages_optional, (), {})
                        ],
                    )
                )
            elif i == _FileChooserButtonIndex.SUBTITLE.value:
                filechooser_list.append(
                    _CustomFileChooser(
                        parent = self,
                         # callbacks without args or kwargs
                        deselection_callbacks = [
                            (self.reset_available_languages_target, (), {})
                        ],
                    )
                )
            elif i == _FileChooserButtonIndex.OPTIONAL_SUBTITLE.value:
                filechooser_list.append(
                    _CustomFileChooser(
                        parent = self,
                         # callbacks without args or kwargs
                        deselection_callbacks = [
                            (self.reset_available_languages_optional, (), {})
                        ],
                    )
                )
            else:
                filechooser_list.append(_CustomFileChooser(parent = self))

        for (i, filechooser) in enumerate(filechooser_list):
            filechooser.set_hexpand(True)
            set_widget_margin(
                filechooser,
                DISPLAY_WIDTH * 0.005,
                DISPLAY_WIDTH * 0.0025,
                DISPLAY_WIDTH * 0.005,
                DISPLAY_WIDTH * 0.0025
            )
            filechooser.set_halign(Align.FILL)
            self._main_grid.attach(filechooser, 1, i, 1, 1)

        return filechooser_list


    def _setup_filters(self) -> None:
        """
        _setup_filters

        Set a filter for each file chooser.

        :return:
        """

        file_filter1: FileFilter = FileFilter()
        file_filter2: FileFilter = FileFilter()
        file_filter3: FileFilter = FileFilter()

        file_filter1.set_name('collection.anki2')
        file_filter1.add_pattern('*.anki2')
        file_filter2.set_name('Video File')
        file_filter2.add_mime_type('video/mp4')
        file_filter2.add_mime_type('video/wmv')
        file_filter2.add_mime_type('video/avi')
        file_filter2.add_mime_type('video/mkv')
        file_filter2.add_mime_type('video/webm')
        file_filter2.add_pattern('*.mp4')
        file_filter2.add_pattern('*.wmv')
        file_filter2.add_pattern('*.avi')
        file_filter2.add_pattern('*.mkv')
        file_filter2.add_pattern('*.webm')
        file_filter3.set_name('Subtitles (ASS/SRT)')
        file_filter3.add_pattern('*.srt')
        file_filter3.add_pattern('*.ass')
        self._filechoosers_list[_FileChooserButtonIndex.ANKI2_COLLECTION].add_file_filter(file_filter1)
        self._filechoosers_list[_FileChooserButtonIndex.VIDEO].add_file_filter(file_filter2)
        self._filechoosers_list[_FileChooserButtonIndex.SUBTITLE].add_file_filter(file_filter3)
        self._filechoosers_list[_FileChooserButtonIndex.OPTIONAL_SUBTITLE].add_file_filter(file_filter3)


    def _fill_cached_file(self) -> None:
        """
        _fill_cached_file

        Fills up the filechooser's fields from recently used files.

        :return:
        """

        recently_used_files: dict[str, str] | None = handle_exception_if_any(
            "",
            False,
            get_recently_used_files
        )

        if not recently_used_files: return

        anki_collection_filepath: OptionalFilepath = recently_used_files.get("anki_collection_filepath")
        video_filepath: OptionalFilepath = recently_used_files.get("video_filepath")
        subtitles_filepath: OptionalFilepath = recently_used_files.get("subtitles_filepath")
        optional_subtitles_filepath: OptionalFilepath = recently_used_files.get("optional_subtitles_filepath")
        deck_name: OptionalFilepath = recently_used_files.get("deck_name")

        if anki_collection_filepath:
            self._filechoosers_list[_FileChooserButtonIndex.ANKI2_COLLECTION]\
            .set_filename(anki_collection_filepath)

        if video_filepath:
            self._filechoosers_list[_FileChooserButtonIndex.VIDEO].set_filename(video_filepath)

        if subtitles_filepath:
            self._filechoosers_list[_FileChooserButtonIndex.SUBTITLE].set_filename(subtitles_filepath)

        if optional_subtitles_filepath:
            self._filechoosers_list[_FileChooserButtonIndex.OPTIONAL_SUBTITLE]\
            .set_filename(optional_subtitles_filepath)

        if deck_name:
            self._entry.set_text(deck_name)


    def _setup_buttons_signals(self) -> None:
        """
        _setup_buttons_signals

        Set up the buttons and their respective signals for both grids.

        :param win: A window.
        :param fst_grid: The first grid container where the buttons goes in.
        :param box: The box container where the first grid goes in.
        :param fc_s: A list with file choosers.
        :return:
        """

        gicon: Icon = Icon.new_for_string(path.join(ICONS_SYMBOLIC_DIRECTORY, "delete-symbolic.svg"))
        icons: list[Image | None] = [ Image().new_from_gicon(gicon) for _ in range(4) ]
        buttons_list: list[Button] = [ Button() for _ in range(4) ]
        box: Box = Box(orientation=Orientation.HORIZONTAL, halign=Align.CENTER)
        empty_box: Box = Box()
        frame: Frame = Frame(child=box)
        cancel_button: Button = Button(label='Cancel')
        self._next_button = Button(label='Next')

        for (i, button) in enumerate(buttons_list):
            button.set_child(icons[i])
            set_widget_margin(
                button,
                DISPLAY_WIDTH * 0.005,
                DISPLAY_WIDTH * 0.0025,
                DISPLAY_WIDTH * 0.005,
                DISPLAY_WIDTH * 0.0025
            )
            button.set_halign(Align.END)
            self._main_grid.attach(button, 3, i, 1, 1)

        buttons_list[_FileChooserButtonIndex.ANKI2_COLLECTION].connect(
            'clicked',
            lambda _: self._filechoosers_list[_FileChooserButtonIndex.ANKI2_COLLECTION].unselect_all()
        )
        buttons_list[_FileChooserButtonIndex.VIDEO].connect(
            'clicked',
            lambda _: self._filechoosers_list[_FileChooserButtonIndex.VIDEO].unselect_all()
        )
        buttons_list[_FileChooserButtonIndex.SUBTITLE].connect(
            'clicked',
            lambda _: self._filechoosers_list[_FileChooserButtonIndex.SUBTITLE].unselect_all()
        )
        buttons_list[_FileChooserButtonIndex.OPTIONAL_SUBTITLE].connect(
            'clicked',
            lambda _: self._filechoosers_list[_FileChooserButtonIndex.OPTIONAL_SUBTITLE].unselect_all()
        )
        empty_box.set_vexpand(True)
        self._main_box.append(empty_box)
        box.append(cancel_button)
        box.append(self._next_button)
        self._main_box.append(frame)
        cancel_button.connect('clicked', lambda _: self.close())
        set_widget_margin(
            cancel_button,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.1,
            DISPLAY_WIDTH * 0.005
        )
        set_widget_margin(
            self._next_button,
            DISPLAY_WIDTH * 0.1,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.005
        )
        self._next_button.connect('clicked', self._on_next_button_clicked)
        timeout_add(300, self._setup_sensitive_next_button)
        timeout_add(300, self._check_invalid_selection)


    def _setup_text_entry(self) -> None:
        """
        _setup_text_entry

        Sets the text entry for deck name.

        :return:
        """

        self._entry = Entry(placeholder_text='Deck name...')

        set_widget_margin(
            self._entry,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.0025,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.0025
        )
        self._main_grid.attach(self._entry, 1, 4, 1, 1)


    def _setup_dropdowns(self) -> None:
        """
        _setup_dropdown

        Sets the dropdown for Languages selection.

        :return:
        """

        string_target: StringList = StringList()
        string_optional: StringList = StringList()
        self._dropdown_target = DropDown.new(model=string_target)
        self._dropdown_optional = DropDown.new(model=string_optional)

        self._dropdown_target.connect("notify::selected-item", self._on_dropdown_target_item_selected)
        self._dropdown_optional.connect("notify::selected-item", self._on_dropdown_optional_item_selected)
        set_widget_margin(
            self._dropdown_target,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.0025,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.0025
        )
        set_widget_margin(
            self._dropdown_optional,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.0025,
            DISPLAY_WIDTH * 0.005,
            DISPLAY_WIDTH * 0.0025
        )
        self._main_grid.attach(self._dropdown_target, 2, 2, 1, 1)
        self._main_grid.attach(self._dropdown_optional, 2, 3, 1, 1)


    def set_available_languages_target(self) -> None:
        """
        set_available_languages_target

        Setup the dropdown for the target languages if they are available.

        :return:
        """

        list_model: StringList | None = cast(StringList, self._dropdown_target.get_model())
        video_filepath: Filepath  = self.get_filepath(_FileChooserButtonIndex.VIDEO)
        self._available_languages = get_available_encoded_languages(video_filepath)
        languages: list[str] = ["N/a"] + [key for key, _ in self._available_languages.items()]

        list_model.splice(0, list_model.get_n_items(), languages)


    def set_available_languages_optional(self) -> None:
        """
        set_available_languages_optional

        Setup the dropdown for the optional languages if they are available.

        :return:
        """

        list_model: StringList | None = cast(StringList, self._dropdown_optional.get_model())
        video_filepath: Filepath  = self.get_filepath(_FileChooserButtonIndex.VIDEO)
        self._available_languages = get_available_encoded_languages(video_filepath)
        languages: list[str] = ["N/a"] + [key for key, _ in self._available_languages.items()]

        list_model.splice(0, list_model.get_n_items(), languages)


    def reset_available_languages_target(self) -> None:
        """
        reset_available_languages_target

        Select the default option and resets the senstive status.

        :return:
        """

        list_model: StringList | None = cast(StringList, self._dropdown_target.get_model())
        video_filepath: Filepath  = self.get_filepath(_FileChooserButtonIndex.VIDEO)
        self._available_languages = get_available_encoded_languages(video_filepath)
        languages: list[str] = ["N/a"] + [key for key, _ in self._available_languages.items()]

        self._dropdown_target.set_selected(0)
        self._dropdown_target.set_sensitive(True)
        list_model.splice(0, list_model.get_n_items(), languages)


    def reset_available_languages_optional(self) -> None:
        """
        reset_available_languages_optional

        Select the default option and resets the senstive status.

        :return:
        """

        list_model: StringList | None = cast(StringList, self._dropdown_optional.get_model())
        video_filepath: Filepath  = self.get_filepath(_FileChooserButtonIndex.VIDEO)
        self._available_languages = get_available_encoded_languages(video_filepath)
        languages: list[str] = ["N/a"] + [key for key, _ in self._available_languages.items()]

        self._dropdown_optional.set_selected(0)
        self._dropdown_optional.set_sensitive(True)
        list_model.splice(0, list_model.get_n_items(), languages)


    def _wait_for_subtitle_file_creation(self, process: Popen[bytes]) -> None:
        """
        _wait_for_subtitle_file_creation

        Wait for the ffmpeg process to finish.
        While the thread is busy the main thread spawns a loading screen,
        which will be hidden once the job is done.

        :param process: ffmpeg process for creating the subtitles.
        :return:
        """

        idle_add(self._main_box.set_sensitive, False)
        idle_add(self._loading_screen.show_loading_screen)
        process.wait(40) # wait up to 40 seconds before giving up
        idle_add(self._loading_screen.hide_loading_screen)
        idle_add(self._main_box.set_sensitive, True)


    def _threaded_subtitle_creation(self, process: Popen[bytes]) -> None:
        """
        _threaded_subtitle_creation

        Creates a thread to wait for the ffmpeg process to finish its job.

        :param process: ffmpeg process for creating the subtitles.
        :return:
        """

        Thread(target=self._wait_for_subtitle_file_creation, args=(process,), daemon=True).start()


    def _on_dropdown_target_item_selected(self, dropdown: DropDown, _: ParamSpec) -> None:
        """
        _on_dropdown_target_item_selected

        Handles items selection from the dropdown.

        :param dropdown: The dropdown widget that sent the signal.
        :param param_spec: Metadata about the property that triggered the signal.
        :return:
        """

        selected_index: int = dropdown.get_selected()
        subtitle_filechooser: _CustomFileChooser = self._filechoosers_list[_FileChooserButtonIndex.SUBTITLE]
        video_filepath: Filepath  = self.get_filepath(_FileChooserButtonIndex.VIDEO)
        selected_item: StringObject | None = cast(StringObject | None, dropdown.get_selected_item())

        if selected_index != 0 and selected_item:
            selection: str = selected_item.get_string()
            stream_index: str = self._available_languages[selection]["index"]
            language: str = self._available_languages[selection]["language"]
            codec_name: str = self._available_languages[selection]["codec_name"]
            dropdown.set_sensitive(False)
            subtitle_filechooser.set_sensitive(False)

            subtitle_filepath: Filepath | None
            process: Popen[bytes] | None

            subtitle_filepath, process = write_subtitle_file(
                video_filepath,
                stream_index,
                language,
                codec_name
            ) or (None, None)

            dropdown.set_sensitive(True)

            if process and subtitle_filepath:
                self._threaded_subtitle_creation(process)
                subtitle_filechooser.set_filename(subtitle_filepath)

                return

            _print(f"Failed to write the subtitle file for the selected language.", True)

            return

        subtitle_filechooser.set_sensitive(True)


    def _on_dropdown_optional_item_selected(self, dropdown: DropDown, _: ParamSpec) -> None:
        """
        _on_dropdown_optional_item_selected

        Handles items selection from the dropdown.

        :param dropdown: The dropdown widget that sent the signal.
        :param param_spec: Metadata about the property that triggered the signal.
        :return:
        """

        selected_index: int = dropdown.get_selected()
        selected_item: StringObject | None = cast(StringObject | None, dropdown.get_selected_item())

        optional_subtitle_filechooser: _CustomFileChooser = self._filechoosers_list[_FileChooserButtonIndex.OPTIONAL_SUBTITLE]
        video_filepath: Filepath  = self.get_filepath(_FileChooserButtonIndex.VIDEO)

        if selected_index != 0 and selected_item:
            selection: str = selected_item.get_string()
            stream_index: str = self._available_languages[selection]["index"]
            language: str = self._available_languages[selection]["language"]
            codec_name: str = self._available_languages[selection]["codec_name"]
            dropdown.set_sensitive(False)
            optional_subtitle_filechooser.set_sensitive(False)

            subtitle_filepath: Filepath | None
            process: Popen[bytes] | None

            subtitle_filepath, process = write_subtitle_file(
                video_filepath,
                stream_index,
                language,
                codec_name
            ) or (None, None)

            dropdown.set_sensitive(True)

            if process and subtitle_filepath:
                self._threaded_subtitle_creation(process)
                optional_subtitle_filechooser.set_filename(subtitle_filepath)

                return

            _print(f"Failed to write the subtitle file for the selected language.", True)

            return

        optional_subtitle_filechooser.set_sensitive(True)


    def get_filepath(self, filechooser_button_index: _FileChooserButtonIndex) -> Filepath:
        """
        get_filepath

        Return the name of the file.

        :param filechooser_button_index: The index of the filechooser button.
        :return: The name of the file.
        """

        return self._filechoosers_list[filechooser_button_index].get_filepath()


    def get_deck_name(self) -> str:
        """
        get_deck_name

        Gets the deck name.

        :return: The deck name.
        """

        return self._entry.get_text()


    def _check_invalid_selection(self) -> bool:
        """
        _check_invalid_selection

        Unselects any invalid filename selected through file choosers.

        :return: True to keep timeout_add running.
        """

        anki_collection_filepath: Filepath = self.get_filepath(_FileChooserButtonIndex.ANKI2_COLLECTION)
        video_filepath: Filepath  = self.get_filepath(_FileChooserButtonIndex.VIDEO)
        subtitles_filepath: Filepath  = self.get_filepath(_FileChooserButtonIndex.SUBTITLE)
        optional_subtitle_filepath: Filepath = self.get_filepath(_FileChooserButtonIndex.OPTIONAL_SUBTITLE)

        if anki_collection_filepath and not is_file_collection(anki_collection_filepath):
            self._filechoosers_list[_FileChooserButtonIndex.ANKI2_COLLECTION].unselect_all()

        if video_filepath and not is_file_video(video_filepath):
            self._filechoosers_list[_FileChooserButtonIndex.VIDEO].unselect_all()

        if subtitles_filepath and not is_file_subtitles(subtitles_filepath):
            self._filechoosers_list[_FileChooserButtonIndex.SUBTITLE].unselect_all()

        if optional_subtitle_filepath and not is_file_subtitles(optional_subtitle_filepath):
            self._filechoosers_list[_FileChooserButtonIndex.OPTIONAL_SUBTITLE].unselect_all()

        return True


    def _setup_sensitive_next_button(self) -> bool:
        """
        _setup_sensitive_next_button

        Set if a button is clickable or not.

        :return: True to keep timeout_add running.
        """

        is_anki_collection: bool = is_file_collection(self.get_filepath(_FileChooserButtonIndex.ANKI2_COLLECTION))
        is_video: bool = is_file_video(self.get_filepath(_FileChooserButtonIndex.VIDEO))
        is_subtitle: bool = is_file_subtitles(self.get_filepath(_FileChooserButtonIndex.SUBTITLE))
        deck_name: str  = self.get_deck_name()

        if all((is_anki_collection, is_video, is_subtitle, deck_name)):
            self._next_button.set_sensitive(True)
        else:
            self._next_button.set_sensitive(False)

        return True


    def _on_next_button_clicked(self, _: Button) -> None:
        """
        _on_button_clicked

        Handles the clicked event emitted by next_button.

        :param next_button: Button that emitted the event.
        :return:
        """

        anki_collection_filepath: Filepath = self.get_filepath(_FileChooserButtonIndex.ANKI2_COLLECTION)
        video_filepath: Filepath = self.get_filepath(_FileChooserButtonIndex.VIDEO)
        subtitle_filepath: Filepath = self.get_filepath(_FileChooserButtonIndex.SUBTITLE)
        optional_subtitle_filepath: OptionalFilepath = self.get_filepath(_FileChooserButtonIndex.OPTIONAL_SUBTITLE)
        deck_name: str = self.get_deck_name()

        # This should never happen
        if not anki_collection_filepath or not video_filepath or not subtitle_filepath or not deck_name:
            _print("No essential filenames provided, nothing done.")
            return

        cache_recently_used_files(
            anki_collection_filepath,
            video_filepath,
            subtitle_filepath,
            deck_name,
            optional_subtitle_filepath
        )

        CardsEditor(
            self,
            self._app,
            anki_collection_filepath,
            video_filepath,
            subtitle_filepath,
            optional_subtitle_filepath,
            deck_name,
        ).show_all()


__all__: list[str] = ["_CustomFileChooser"]

