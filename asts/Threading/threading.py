from anki.collection import Collection
from anki.notes import Note
from anki.errors import DBError
from anki.models import NotetypeDict

from concurrent.futures import Future, ThreadPoolExecutor
from gi.repository.GLib import idle_add
from multiprocessing    import Manager
from os                 import path
from threading          import Lock, Thread
from typing             import Dict, List, Tuple

from asts.Gui         import AnkiDialog, CardsGenerator
from asts.TypeAliases import *
from asts.Utils       import clearCachedFiles, cut


class ThreadingHandler(Thread):
    def __init__(self, handler: CardsGenerator, chunk_size: int = 5, nthreads: int = 2):
        super().__init__()

        self._handler = handler

        self._deck: Collection

        # the size of the block of tasks to be executed
        self._chunk_size = chunk_size

        # number of threads to be used
        self._nthreads = nthreads

        self.start()


    @staticmethod
    def _createCard(
            card: Note,
            sentence_front: str,
            sentence_back: str,
            media_video: OptVideoFile,
            media_audio: OptMp3File,
            media_image: OptMbpFile
    ) -> None:
        """
        Create a new anki card.

        :param card: An empty card to be filled.
        :param sentence_front: Optional phrase to the front of the card.
        :param sentence_back: Optional phrase to the back of the card.
        :param media_video: Optional filename to a video media file.
        :param media_audio: Optional filename to an audio media file.
        :param media_image: Optional filename to an image media file.
        :return:
        """

        card_fields: List[Dict[str, str]]   = card.note_type()['flds']
        card_front: str                     = card_fields[0]['name']
        card_back: str                      = card_fields[1]['name']

        sentence_front = sentence_front.replace('\n', '<br>')
        sentence_back = sentence_back.replace('\n', '<br>')

        if media_video:
            card[card_front] = sentence_front
            card[card_back]  = f'[sound:{media_video}]' + '<br><br>' + sentence_back
        elif media_audio and media_image:
            card[card_front] = sentence_front           + '<br><br>' + f'[sound:{media_audio}]'
            card[card_back] = f'<img src={media_image}>'+ '<br><br>' + sentence_back
        elif media_audio and not media_image:
            card[card_front] = sentence_front           + '<br><br>' + f'[sound:{media_audio}]'
            card[card_back] = sentence_back
        else:
            card[card_front] = sentence_front
            card[card_back] = f'<img src="{media_image}">'  + '<br><br>' + sentence_back


    def _writeCard(self, tuple_sentence: Tuple[str, str, OptVideoFile, OptMp3File, OptMbpFile], lock: Lock) -> None:
        """
        Create write a new card to the anki.collection.
        Can raise exception StopAsyncIteration in case of cancelling tasks.

        :param tuple_sentence: A tuple that contain info about constructing a front/back card.
        :param lock: Lock the process until it finish it's work.
        :return:
        """

        # the database needs to write cards one by one
        # we need to lock here to ensure that no more than one card
        # it's being write, otherwise DBError will be raised
        with lock:
            video: OptVideoFile      = None
            audio: OptMp3File        = None
            image: OptMbpFile        = None
            media_video: OptFilename = None
            media_audio: OptFilename = None
            media_image: OptFilename = None

            sentence_front: str
            sentence_back: str

            (sentence_front, sentence_back, video, audio, image) = tuple_sentence

            if video:
                media_video = self._deck.media.add_file(self.cache_dir + '/' + video)

            if audio:
                media_audio = self._deck.media.add_file(self.cache_dir + '/' + audio)

            if image:
                media_image = self._deck.media.add_file(self.cache_dir + '/' + image)

            card: Note = self._deck.newNote()

            self._createCard(card, sentence_front, sentence_back, media_video, media_audio, media_image)
            self._deck.addNote( card )


    def _cutMedias(self, vid_filename: Filename, list_of_medias: List[List[Info]]) -> None:
        """
        Cut the clip selected to be used at the creation of cards.

        :param vid_filename: the filename of the clip to be used.
        :param list_of_medias: a list with the filenames of the clips to be cutted.
        :return:
        """

        chunked_medias: List[List[List[Info]]] = [
            list_of_medias[i : (i + self._chunk_size)]
            for i in range(0, len(list_of_medias), self._chunk_size)
        ]

        for chunk_of_medias in chunked_medias:
            with ThreadPoolExecutor(self._nthreads) as executor:
                for media_info in chunk_of_medias:
                    if not self._handler.getCancelTaskStatus():

                        future: Future = executor.submit(
                            cut,
                            vid_filename,
                            media_info
                        )

                        self._handler.appendFuture(future)

                        future.add_done_callback(self._handler.idleaddUpdateProgress)
                    else:
                        return


    def _prepareCards(
        self,
        coll_filename: Filename,
        deck_name: str,
        list_of_sentences:
        List[
            Tuple[
                str,
                str,
                OptVideoFile,
                OptMp3File,
                OptMbpFile
            ]
        ]
    ) -> None:
        """
        Setup info to create anki cards.

        :param coll_filename: Path to the anki.collection.
        :param list_of_sentences: A list with info about the sentences to be constructed.
        :return:
        """

        self.cache_dir: str = path.abspath('data/cache/media')

        # Collection actually changes the directory
        # to the anki.collection path
        self._deck           = Collection( coll_filename )

        deck_id: int        = self._deck.decks.id( deck_name )
        self._deck.decks.select( deck_id )
        card_type: str      = self._deck.models.current()['name']
        model: NotetypeDict = self._deck.models.by_name( card_type )
        model['did']        = deck_id
        self._deck.models.save( model )
        self._deck.models.set_current( model )

        chunked_senteces: List[
            List[
                Tuple[
                    str,
                    str,
                    OptVideoFile,
                    OptMp3File,
                    OptMbpFile
                ]
            ]
        ] = [

            list_of_sentences[i : (i + self._chunk_size)]

            for i in range(0, len(list_of_sentences), self._chunk_size)
        ]

        for chunk_of_sentences in chunked_senteces:
            with ThreadPoolExecutor(self._nthreads) as executor:
                lock: Lock = Manager().Lock()

                for sentence in chunk_of_sentences:
                    if not self._handler.getCancelTaskStatus():
                        future: Future = executor.submit(self._writeCard, sentence, lock)

                        self._handler.appendFuture(future)

                        future.add_done_callback(self._handler.idleaddUpdateProgress)
                    else:
                        return


    def _cleaning(self) -> None:
        """
        Clear the files used to create cards and close the deck.

        :return:
        """

        # let cleaning close the deck, otherwise
        # case the tasks are cancelled it wouldn't be closed
        try:
            self._deck.close()
        # it's possible that the deck was not opened at all
        # in case the Anki application is already running
        # so it's ok pass here
        except AttributeError:
            pass

        clearCachedFiles()


    def _dbErrorDialog(self) -> None:
        """
        Display a dialog indicating the Anki database is opened.

        :return:
        """

        idle_add(self._handler.resetProgressbar)

        idle_add(AnkiDialog(self._handler).showAll)


    def run(self) -> None:
        """
        Method representing the thread's activity.

        :return:
        """

        # reset cancel status in case it was cancelled before
        self._handler.setCancelTaskStatus(False)

        self._cutMedias(self._handler.getVideoFilename(), self._handler.getListInfoMedias())

        try:
            self._prepareCards(self._handler.getCollection(), self._handler.getDeckName(), self._handler.getListOfSentences())

        #This will call a function that will draw a dialog window case anki is already opened
        except DBError:
            self._dbErrorDialog()

        self._cleaning()

