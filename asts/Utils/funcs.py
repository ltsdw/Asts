from __future__ import annotations

from glob       import glob

from io                 import TextIOWrapper
from pysrt              import open as popen
from pysrt              import SubRipItem
from pyasstosrt         import Subtitle, Dialogue
from os                 import mkdir, path, remove, system
from typing             import List, Optional, Union

from asts.TypeAliases import (
    Command,
    Filename,
    Filepath,
    Info,
    OptFilename
)


def isCollection(collection_filename: OptFilename = None) -> bool:
    """
    Returns true if is anki2.collection.

    :param collection_filename: Path to the anki collection.
    :return: True if it is anki2.collection.
    """

    if collection_filename:
        if 'anki2' == collection_filename.split('.')[-1]:
            return True

    return False

def isVideo(video_filename: OptFilename = None) -> bool:
    """
    Returns true if is a video file.

    :param video_filename: Path to the video file.
    :return: True if it is video file.
    """

    if video_filename:
        if video_filename.split('.')[-1] in ('mp4', 'wmv', 'avi', 'mkv', 'webm'):
            return True

    return False

def isSub(sub_filename: OptFilename = None) -> bool:
    """
    Returns true if is a subtitle file.

    :param sub_filename: Path to the subtitle file.
    :return: True if it is subtitle file.
    """

    if sub_filename:
        if 'srt' == sub_filename.split('.')[-1]:
            return True

        if 'ass' == sub_filename.split('.')[-1]:
            return True

    return False

def createCacheDirIfItNotExists() -> None:
    """
    Create the directory used to cache files used to create cards.

    :return:
    """

    if not path.exists(path.abspath('data')):
        mkdir('data')

    if not path.exists(path.abspath('data/cache')):
        mkdir('data/cache')

    if not path.exists(path.abspath('data/cache/media')):
        mkdir('data/cache/media')

def recentUsedFiles(
        anki_collection_filename: Filename,
        deck_name: str) -> None:
    """
    Write the video filename and deck name to a file.

    :param anki_collection_filename: Path to the anki.collection.
    :param deck_name: Name of the deck.
    :return:
    """

    cache_dir: Filepath = path.abspath('data/cache')
    data: str = f'{anki_collection_filename}\n{deck_name}'

    with open(cache_dir + '/' + 'cached_usage.txt', 'w+') as f:
        f.write(data)

def clearCachedFiles() -> None:
    """
    Remove all files used at the creation of cards.

    :return:
    """

    # maybe isn't any file to delete.
    # it's safe to pass here.
    try:
        cache_dir: Filepath       = path.abspath('data/cache')
        cache_media_dir: Filepath = path.join(cache_dir + '/' + 'media' + '/')
        files: List[Filename]     = glob(cache_media_dir + '/' + '*')

        for file in files:
            remove(file)

    except FileNotFoundError:
        pass

def cut(input_file: Filename, media_info: List[Info]) -> None:
    """
    Cut the video making a short clip, audio or image.

    :param input_file: Name of the video to be used.
    :media_info: A list with info about how the final media will be.
    :return:
    """

    cmd: Command

    cache_dir: Filepath   = path.abspath('data/cache/media')
    output_file: Filepath = cache_dir + '/' + str(media_info[0])

    start: Info       = media_info[2]
    end: Info         = media_info[3]
    video: Info       = media_info[4]
    audio: Info       = media_info[5]
    snapshot: Info    = media_info[6]

    if video:
        cmd = f"ffmpeg -v quiet -y -i '{input_file}' -ss {start} -to {end} -vf scale=640:-1 -async 1 {output_file}.mp4"
        system(cmd)

    if audio:
        cmd = f"ffmpeg -v quiet -y -i '{input_file}' -vn -ss {start} -to {end} -b:a 320k {output_file}.mp3"
        system(cmd)

    if snapshot:
        cmd = f"ffmpeg -v quiet -y -ss {start} -i '{input_file}' -vsync 0 -vframes 1 -filter:v scale=640:-1 {output_file}.bmp"
        system(cmd)

def _checkIfIsAss(sub_filename: OptFilename = None) -> bool:
    """
    Returns true if is a .ass subtitle file.

    :param sub_filename: Path to the .ass subtitle file.
    :return: True if it is .ass subtitle file.
    """

    if sub_filename:
        if 'ass' in sub_filename.split('.')[-1]:
            return True

    return False

def _openSubFile(f_path: Filename) -> List[TextIOWrapper]:
    """
    Opens the subtitle file.

    :param f_path: Subtitle path file.
    :return: A list of the dialogues.
    """

    if _checkIfIsAss(f_path):
        return Subtitle(f_path).export(output_dialogues=True)

    return popen(f_path)

def _listDialogue(opened_sub_indexed: Union[SubRipItem, Dialogue]) -> List[str]:
    """
    Separete each items that form a dialogue into a list.

    :return: A list of dialogues.
    """

    return str(opened_sub_indexed).split('\n')

def _extractDialogue(subtitle: List[str]) -> List[Info]:
    """
    Fills up info about the dialogue.

    :param subtitle: Subtitle.
    :return: Optional list with the dialogue info.
    """

    final_sub: List[Info] = []

    # concatenate the dialogues separating it by a new line
    # but only if the dialogue isn't empty then concatenate that
    # to the rest of the list
    list_sub: List[str] = subtitle[:2] + ['\n'.join(dialogue for dialogue in subtitle[2:] if dialogue)]

    # this line here checks whether the dialogues is only a song
    # generally appears as '♪～'
    if len(list_sub[2]) > 3:
        timers: List[str] = list_sub[1].split('-->')
        start_timer: str  = timers[0].replace(',','.')
        end_timer: str    = timers[1].replace(',','.')

        final_sub.append(int(list_sub[0]))  # indice
        final_sub.append(list_sub[2])       # dialogue
        final_sub.append(start_timer)       # start timer
        final_sub.append(end_timer)         # end timer
        final_sub = final_sub + [False, False, False] # video, audio, image

    return final_sub

def extractAllDialogues(f_path: Filename) -> List[List[Info]]:
    """
    Returns all dialogues from f_path parsed.

    :param f_path: Filename of the subtitle file.
    :return: A list with the parsed dialogues.
    """

    dialogues_list: List[List[Info]] = []

    open_sub: List[TextIOWrapper] = _openSubFile(f_path)

    for (i,_) in enumerate(open_sub):
        dialogue: List[Info] = _extractDialogue(_listDialogue(open_sub[i]))
        if dialogue:
            dialogues_list.append(dialogue)

    return dialogues_list

def serializeIt(text_buffer: TextBuffer, tmp_string: Optional[str] = None) -> bytes:
    """
    Serializes the text_buffer.

    :param text_buffer: The text buffer where the data will be extracted to be serializeed.
    :param tmp_string: Temporary string.
    :return: Serialized data.
    """

    if tmp_string:
        text_buffer.set_text(tmp_string)

        tmp_start_iter: TextIter  = text_buffer.get_start_iter()
        tmp_end_iter: TextIter    = text_buffer.get_end_iter()
        tmp_format: bytes         = text_buffer.register_serialize_tagset()

        tmp_exported: bytes = text_buffer.serialize(
                text_buffer,
                tmp_format,
                tmp_start_iter,
                tmp_end_iter
        )

        return tmp_exported

    else:
        start_iter: TextIter    = text_buffer.get_start_iter()
        end_iter: TextIter      = text_buffer.get_end_iter()
        format: bytes           = text_buffer.register_serialize_tagset()

        exported: bytes = text_buffer.serialize(
            text_buffer,
            format,
            start_iter,
            end_iter
        )

        return exported

def deserializeIt(text_buffer: TextBuffer, exported: bytes) -> None:
    """
    Deserialize the text_buffer.

    :param text_buffer: The text buffer where the data deserialized will be inserted.
    :param exported: The data to be deserialized.
    :return:
    """

    # we need clear the buffer before adding more text.
    # also the last caracter can't be null
    # otherwise any tag applied will be removed.
    text_buffer.set_text('\n')

    text_buffer.deserialize(
        text_buffer,
        text_buffer.register_deserialize_tagset(),
        text_buffer.get_start_iter(),
        exported
    )

    # as we don't want that new line character to be at the current buffer anymore
    # we delete it.
    end_iter: TextIter = text_buffer.get_end_iter()
    text_buffer.backspace(end_iter, False, True)

def setMargin(
    widget: Widget,
    start: int = 0,
    top: Optional[int] = None,
    end: Optional[int] = None,
    bottom: Optional[int] = None
) -> None:
    """
    Sets the margin for the widget.
    If any parameter is missing it will be setted to the value of the first parameter.

    :param widget: Widget to be used.
    :param start: The start margin.
    :param top: The top margin.
    :param end: The end margin.
    :param bottom: The bottom margin.
    :returm:
    """

    # they may be 0 so explicitly compare with None

    if top == None:
        top = start

    if end == None:
        end = start

    if bottom == None:
        bottom = start

    widget.set_margin_start(start)
    widget.set_margin_top(top)
    widget.set_margin_end(end)
    widget.set_margin_bottom(bottom)

