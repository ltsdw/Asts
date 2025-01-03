from anki.collection import Collection
from anki.decks import DeckId
from anki.notes import Note
from anki.models import NotetypeDict

from concurrent.futures import Future, ThreadPoolExecutor
from os                 import path
from threading          import Lock, Thread
from typing             import cast, Callable, Generator

from asts.custom_typing.globals import (
    CACHE_MEDIA_DIR, VIDEO_FORMAT, AUDIO_FORMAT, IMAGE_FORMAT
)
from asts.utils.core_utils import _print, get_chunked, NEW_LINE
from asts.utils.extra_utils import cut_video, remove_cached_media_files
from asts.custom_typing.aliases  import (
    OptionalFilename, Filepath, OptionalVideoFilepath,
    OptionalAudioFilepath, OptionalImageFilepath,
)
from asts.custom_typing.card_info import CardInfo, CardInfoIndex
from asts.custom_typing.dialogue_info import DialogueInfo, DialogueInfoIndex
from asts.custom_typing.typed_list_store import TypedListStore
from asts.custom_typing.cards_editor_states import CardsEditorState, CardsEditorStates
from asts.custom_typing.pango_markup_to_html import PangoMarkupToHTML


class CardsGenerator(Thread):
    def __init__(
        self,
        anki_collection_filepath: Filepath,
        video_filepath: Filepath,
        _dialogue_info_list_store_front: TypedListStore[DialogueInfo],
        _dialogue_info_list_store_back: TypedListStore[DialogueInfo],
        deck_name: str,
        cards_editor_state: CardsEditorState,
        idle_add_update_progress_bar: Callable[[int, int], None],
        max_workers: int = 2
    ) -> None:
        """
        CardsGenerator

        Creates Anki's cards and its media files concurrently.

        :param anki_collection_filepath: Anki's collection filepath.
        :param video_filepath: Video filepath.
        :param _dialogue_info_list_store_front: ListStore object filled with DialogueInfo objects.
        :param _dialogue_info_list_store_back: ListStore object filled with DialogueInfo objects.
        :param deck_name: Anki's deck name.
        :param cards_editor_state: State object that keeps the track of CardsEditor's class state.
        :param idle_add_update_progress_bar: A callable to be called when Futures are
                                             done to update the CardsEditor's Gtk.ProgressBar.
        :param max_workers: The maximum number of threads that can be used to execute the given calls.
        :return:
        """

        super().__init__()

        self._video_filepath: Filepath = video_filepath
        self._dialogue_info_list_store_front: TypedListStore[DialogueInfo] = _dialogue_info_list_store_front
        self._dialogue_info_list_store_back: TypedListStore[DialogueInfo] = _dialogue_info_list_store_back
        self._deck_name: str = deck_name
        # Collection actually changes the directory
        # to the path of anki_collection_filepath
        self._deck: Collection =  Collection(anki_collection_filepath)
        self._idle_add_update_progress_bar: Callable[[int, int], None] = idle_add_update_progress_bar
        self._lock: Lock
        self._cards_editor_state: CardsEditorState = cards_editor_state
        self._max_workers: int = max_workers
        self._futures_list: list[Future[None]] = []
        self._chunks_card_info_list: list[list[CardInfo]]
        self._total_number_tasks: int = 0
        self._number_completed_tasks: int = 0


    def _create_card(
        self,
        text_front: str,
        text_back: str,
        video_filepath: OptionalVideoFilepath,
        audio_filepath: OptionalAudioFilepath,
        image_filepath: OptionalImageFilepath
    ) -> Note | None:
        """
        _create_card

        Create a new anki card.

        :param text_front: Optional text to the front field of the card.
        :param text_back: Optional text to the back field of the card.
        :param video_filepath: Optional filename to a video media file.
        :param audio_filepath: Optional filename to an audio media file.
        :param image_filepath: Optional filename to an image media file.
        :return:
        """
        note: Note = self._deck.newNote()
        note_type: NotetypeDict | None = note.note_type()

        # In what situation this returns None?
        if not note_type:
            _print("Failed to fetch note type for card. Card wasn't created.")
            return

        card_fields: list[dict[str, str]]   = note_type["flds"]
        card_front: str                     = card_fields[0]["name"]
        card_back: str                      = card_fields[1]["name"]

        text_front = text_front.replace("\n", "<br>")
        text_back = text_back.replace("\n", "<br>")

        if video_filepath:
            note[card_front] = text_front
            note[card_back]  = f"[sound:{video_filepath}]<br><br>{text_back}"
        elif audio_filepath and image_filepath:
            note[card_front] = f"{text_front}<br><br>[sound:{audio_filepath}]"
            note[card_back] = f"<img src={image_filepath}><br><br>{text_back}"
        elif audio_filepath and not image_filepath:
            note[card_front] = f"{text_front}<br><br>[sound:{audio_filepath}]"
            note[card_back] = text_back
        else:
            note[card_front] = text_front
            note[card_back] = f"<img src=\"{image_filepath}\"><br><br>{text_back}"

        return note


    def _write_card(
        self,
        card: CardInfo
    ) -> None:
        """
        _write_card

        Creates and writes a new card to the anki.collection.
        Can raise exception StopAsyncIteration in case of cancelling tasks.

        :param tuple_sentence: A CardInfo object with data related to a specific card.
        :return:
        """

        if self._cards_editor_state.is_state(CardsEditorStates.CANCELLED): return

        # the database needs to write cards one by one
        # we need to lock here to ensure that no more than one card
        # is being written, otherwise DBError will be raised
        with self._lock:
            front_field: str                    = card[CardInfoIndex.FRONT_FIELD]
            back_field: str                     = card[CardInfoIndex.BACK_FIELD]
            video: OptionalVideoFilepath        = card[CardInfoIndex.VIDEO_FILEPATH]
            audio: OptionalAudioFilepath        = card[CardInfoIndex.AUDIO_FILEPATH]
            image: OptionalImageFilepath        = card[CardInfoIndex.IMAGE_FILEPATH]
            video_filepath: OptionalFilename    = None
            audio_filepath: OptionalFilename    = None
            image_filepath: OptionalFilename    = None

            if video:
                video_filepath = self._deck.media.add_file(video)

            if audio:
                audio_filepath = self._deck.media.add_file(audio)

            if image:
                image_filepath = self._deck.media.add_file(image)

            note: Note | None = self._create_card(
                front_field,
                back_field,
                video_filepath,
                audio_filepath,
                image_filepath
            )

            if not note: return

            self._deck.addNote(note)


    def _cut_medias(self, executor: ThreadPoolExecutor) -> None:
        """
        _cut_medias

        Cut the clip selected to be used at the creation of cards.

        :param executor: Pool of threads where all workers will sit.
        :return:
        """

        for card_info_list in self._chunks_card_info_list:
            for card_info in card_info_list:
                future: Future[None] = executor.submit(
                    cut_video,
                    self._video_filepath,
                    card_info,
                    self._cards_editor_state
                )

                self._futures_list.append(future)
                self._add_task()
                future.add_done_callback(self._mark_task_completed)
                future.add_done_callback(self._update_progress_bar_on_done)


    def _prepare_cards(self, executor: ThreadPoolExecutor) -> None:
        """
        _prepare_cards

        Prepare cards to be written to the Anki's collection database.

        :param executor: Pool of threads where all workers will sit.
        :return:
        """

        deck_id: DeckId | None = self._deck.decks.id(self._deck_name)

        # This should never happen
        if not deck_id:
            _print(f"Failed to get deck id for name: {self._deck_name}{NEW_LINE}", True)
            return

        self._deck.decks.select(deck_id)
        card_type: str = self._deck.models.current()["name"]
        model: NotetypeDict | None = self._deck.models.by_name(card_type)

        # This should never happen
        if not model:
            _print(f"Failed to get model for card type: {card_type}{NEW_LINE}", True)
            return

        model["did"] = deck_id

        self._deck.models.save(model)
        self._deck.models.set_current(model)

        for card_info_list in self._chunks_card_info_list:
            for card in card_info_list:
                future: Future[None] = executor.submit(self._write_card, card)

                self._futures_list.append(future)
                self._add_task()
                future.add_done_callback(self._mark_task_completed)
                future.add_done_callback(self._update_progress_bar_on_done)


    def _create_card_info_list(self) -> Generator[CardInfo, None, None]:
        """
        _create_list_cards

        Creates a list of CardInfo objects with information of how the card should be created.

        :return: The newly created list filled with CardInfo objects.
        """

        pango_markup_to_html: PangoMarkupToHTML = PangoMarkupToHTML()

        for dialogue_info_front in self._dialogue_info_list_store_front:
            if not (dialogue_info_front[DialogueInfoIndex.HAS_VIDEO]
                or dialogue_info_front[DialogueInfoIndex.HAS_AUDIO]
                or dialogue_info_front[DialogueInfoIndex.HAS_IMAGE]):
                continue

            index: int = dialogue_info_front.get_index()
            dialogue_info_back: DialogueInfo = cast(
                DialogueInfo,
                self._dialogue_info_list_store_back[index]
            )
            front_field_text: str = pango_markup_to_html.get_text_parsed(
                dialogue_info_front[DialogueInfoIndex.DIALOGUE]
            )
            back_field_text: str = pango_markup_to_html.get_text_parsed(
                dialogue_info_back[DialogueInfoIndex.DIALOGUE]
            )
            card_info: CardInfo = CardInfo(
                front_field=front_field_text,
                back_field=back_field_text
            )

            card_info[CardInfoIndex.START_TIMESTAMP] = dialogue_info_front[DialogueInfoIndex.START_TIMESTAMP]
            card_info[CardInfoIndex.END_TIMESTAMP] = dialogue_info_front[DialogueInfoIndex.END_TIMESTAMP]

            if dialogue_info_front[DialogueInfoIndex.HAS_VIDEO]:
                card_info[CardInfoIndex.VIDEO_FILEPATH] = path.join(
                    CACHE_MEDIA_DIR,
                    f"{dialogue_info_front[DialogueInfoIndex.DIALOGUE_UUID]}{VIDEO_FORMAT}"
                )

            if dialogue_info_front[DialogueInfoIndex.HAS_AUDIO]:
                card_info[CardInfoIndex.AUDIO_FILEPATH] = path.join(
                    CACHE_MEDIA_DIR,
                    f"{dialogue_info_front[DialogueInfoIndex.DIALOGUE_UUID]}{AUDIO_FORMAT}"
                )

            if dialogue_info_front[DialogueInfoIndex.HAS_IMAGE]:
                card_info[CardInfoIndex.IMAGE_FILEPATH] = path.join(
                    CACHE_MEDIA_DIR,
                    f"{dialogue_info_front[DialogueInfoIndex.DIALOGUE_UUID]}{IMAGE_FORMAT}"
                )

            yield card_info


    def _cleaning(self) -> None:
        """
        _cleaning

        Clear the files used to create cards and close the deck.

        :return:
        """

        # let cleaning close the deck, otherwise,
        # case the tasks are cancelled it wouldn't be closed
        try:
            self._deck.close()
        # it's possible that the deck was not open at all
        # in case the Anki application is already running
        # so it's ok pass here
        except AttributeError:
            pass

        remove_cached_media_files()


    def get_total_number_of_tasks(self) -> int:
        """
        get_total_number_of_tasks

        Gets the total number of tasks.

        :return: Total number of tasks.
        """

        return self._total_number_tasks


    def _mark_task_completed(self, _: Future[None]) -> None:
        """
        _mark_task_completed

        Updates the number of completed tasks.

        :param future: The future that was completed.
        :return:
        """

        self._number_completed_tasks += 1


    def _add_task(self) -> None:
        """
        _add_task

        Updates the total number of tasks.

        :return:
        """

        self._total_number_tasks += 1


    def _update_progress_bar_on_done(self, _: Future[None]) -> None:
        """
        _update_progress_bar_on_done

        Callback function to update CardsEditor's progress bar.

        :param future: The future that was completed.
        :return:
        """

        self._idle_add_update_progress_bar(self._number_completed_tasks, self._total_number_tasks)


    #def _db_error_dialog(self) -> None:
    #    """
    #    _db_error_dialog

    #    Display a dialog indicating the Anki database is opened.

    #    :return:
    #    """

    #    idle_add(self._handler.resetProgressbar)

    #    idle_add(AnkiDialog(self._handler).showAll)


    def get_futures_list(self) -> list[Future[None]]:
        """
        get_futures_list

        Returns a list with all futures generated from this class object.

        :return: List with all futures generated from this class object.
        """

        return self._futures_list


    def run(self) -> None:
        """
        run

        Method representing the thread's activity.

        :return:
        """

        try:
            self._cards_editor_state.set_state(CardsEditorStates.RUNNING)

            self._total_number_tasks = 0
            self._number_completed_tasks = 0
            self._lock = Lock()
            self._chunks_card_info_list = get_chunked(
                list(self._create_card_info_list()),
                self._max_workers
            )

            # This can raise Anki's DBError exception,
            # let the higher class using this handle it

            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                self._cut_medias(executor)
                self._prepare_cards(executor)
        finally:
            self._cleaning()
            self._cards_editor_state.set_state(CardsEditorStates.NORMAL)


__all__: list[str] = ["CardsGenerator"]

