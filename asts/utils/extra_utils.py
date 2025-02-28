from asts.custom_typing.globals import GDK_VERSION, GTK_VERSION

from gi import require_version
require_version(*GTK_VERSION)
require_version(*GDK_VERSION)
from gi.repository.Gtk import TextBuffer, TextIter, TextTag, Widget
from gi.repository.Gdk import RGBA as GdkRGBA
from gi.repository.GLib import markup_escape_text
from gi.repository.GLib import Error as GLibError
from gi.repository.Pango import (
    parse_markup, AttrList, AttrColor, AttrIterator,
    AttrInt, AttrType, Style, Underline, Weight
)

from datetime   import datetime, timedelta
from ffmpeg     import probe
from ffmpeg     import input as FFMPEGInput
from ffmpeg     import Error as FFMPEGError
from glob       import glob
from pysrt      import open as popen
from pysrt      import SubRipFile
from pyasstosrt import Subtitle, Dialogue
from os         import makedirs, path, remove
from tomllib    import load
from typing     import Any

from asts.utils.core_utils import NEW_LINE, die, handle_exception_if_any, _print
from asts.custom_typing.aliases import (
    Filename, Filepath, OptionalFilepath,
    OptionalVideoFilepath, OptionalImageFilepath,
    OptionalAudioFilepath, OptionalFilename, OptionalTimestamp
)
from asts.custom_typing.globals import CACHE_MEDIA_DIR, RECENTLY_USED_FILEPATH
from asts.custom_typing.format_tags import FormatTags
from asts.custom_typing.dialogue_info import DialogueInfo
from asts.custom_typing.card_info import CardInfo, CardInfoIndex
from asts.custom_typing.rgba import RGBA
from asts.custom_typing.text_buffer_pango_markup_parser import TextBufferPangoMarkupParser
from asts.custom_typing.cards_editor_states import CardsEditorState, CardsEditorStates
from asts.custom_typing.timestamp_field_info import TimestampFieldInfo


def is_file_collection(filename: OptionalFilename = None) -> bool:
    """
    is_file_collection

    Returns true if the filename ends with anki2.

    :param filename: Path to the anki collection.
    :return: True if it is a collection.anki2.
    """

    if filename:
        return filename.endswith((".anki2"))

    return False


def is_file_video(filename: OptionalFilename = None) -> bool:
    """
    is_file_video

    Returns true if the filename is a video.

    :param filename: Path to the video file.
    :return: True if it is video file.
    """

    if filename:
        return filename.endswith((".mp4", ".wmv", ".avi", ".mkv", ".webm", ".mov"))

    return False


def is_file_subtitles(filename: OptionalFilename = None) -> bool:
    """
    is_file_subtitles

    Returns true if is a subtitle file.

    :param filename: Path to the subtitle file.
    :return: True if it is subtitle file.
    """

    if filename:
        return filename.endswith((".ass", ".srt"))

    return False


def remove_cached_media_files() -> None:
    """
    remove_cached_media_files

    Remove all media files used to create the Anki's cards.

    :return:
    """

    # Maybe there isn't any file to delete,
    # so it's safe to ignore FileNotFoundError here.
    try:
        files: list[Filename] = glob(path.join(CACHE_MEDIA_DIR, "*"))

        for file in files:
            remove(file)
    except FileNotFoundError:
        pass


def cut_video(input_file: Filepath, card_info: CardInfo, cards_editor_state: CardsEditorState) -> None:
    """
    cut_video

    Cut the video making a short clip, audio or image.

    :param input_file: Path of the video to be used.
    :param list_media_info: A list with info about how the final media will be.
    :param cards_editor_state: State object that keeps the track of CardsEditor's class state.
    :return:
    """

    if cards_editor_state.is_state(CardsEditorStates.CANCELLED): return

    start_timestamp: OptionalTimestamp     = card_info[CardInfoIndex.START_TIMESTAMP]
    end_timestamp: OptionalTimestamp       = card_info[CardInfoIndex.END_TIMESTAMP]
    video_filepath: OptionalVideoFilepath  = card_info[CardInfoIndex.VIDEO_FILEPATH]
    audio_filepath: OptionalAudioFilepath  = card_info[CardInfoIndex.AUDIO_FILEPATH]
    image_filepath: OptionalImageFilepath  = card_info[CardInfoIndex.IMAGE_FILEPATH]

    if not start_timestamp and not end_timestamp: return

    try:
        if video_filepath:
            FFMPEGInput(
                input_file,
                ss=start_timestamp,
                to=end_timestamp
            ).output(
                video_filepath,
                vf="scale=640:-1",
            ).global_args(
                "-y",
                "-nostdin",
                "-loglevel",
                "quiet"
            ).run()
        if audio_filepath:
            FFMPEGInput(
                input_file,
                ss=start_timestamp,
                to=end_timestamp
            ).output(
                audio_filepath,
                vn=None,
                b="320k"
            ).global_args(
                "-y",
                "-nostdin",
                "-loglevel",
                "quiet"
            ).run()
        if image_filepath:
            FFMPEGInput(
                input_file,
                ss=start_timestamp,
                to=end_timestamp,
            ).output(
                image_filepath,
                vsync=0,
                vframes=1,
                filter_complex="scale=640:-1"
            ).global_args(
                "-y",
                "-nostdin",
                "-loglevel",
                "quiet"
            ).run()
    except FFMPEGError as e:
        _print(f"Error running ffmpeg probe: {e.stderr.decode()}", True)


def is_ass_file(sub_filepath: OptionalFilepath = None) -> bool:
    """
    is_ass_file

    Returns true if is a .ass subtitle file.

    :param sub_filepath: Path to the .ass subtitle file.
    :return: True if it is .ass subtitle file.
    """

    if sub_filepath:
        return sub_filepath.endswith(".ass")

    return False


def open_sub_file(subtitles_filepath: Filepath) -> list[Dialogue] | SubRipFile | None:
    """
    open_sub_file

    Opens the subtitle file and return its dialogues.

    :param sub_filepath: Subtitle filepath.
    :return: The dialogues or None in case of some failure.
    """

    if is_ass_file(subtitles_filepath):
        return Subtitle(subtitles_filepath).export(output_dir="", output_dialogues=True)

    return popen(subtitles_filepath)


def split_dialogue_line(opened_sub_indexed: SubRipFile | Dialogue) -> list[str]:
    """
    split_dialogue_line

    Splits a line of dialogue at the "\\n" character returning each element inside a list.

    :param opened_sub_indexed:
    :return: A list with each element of the dialogue line [index, start, end, text].
    """

    return str(opened_sub_indexed).split("\n")


def create_dialogue_info(subtitle: list[str]) -> DialogueInfo:
    """
    create_dialogue_info

    Fills up info about the dialogue creating a DialogueInfo object.

    :param subtitle: A list representing a subtitle in the srt format like:
                     [ "0", "00:00:00,000 --> 00:00:00,000", "Some lines of text", "maybe some more text"]
    :return: A DialogueInfo object with its properties set.
    """

    # dialogues = [ "0", "00:00:00,000 --> 00:00:00,000", "Some lines of dialogues", "maybe some more text"]

    _start_time: str
    _end_time: str
    _start_time, _end_time = map(lambda s: s.replace(",", ".").strip(), subtitle[1].split("-->"))
    _dialogue: str = "\n".join(dlg for dlg in subtitle[2:] if dlg)

    card_info: DialogueInfo = DialogueInfo(
        dialogue = markup_escape_text(_dialogue, length = -1),
        start_timestamp_field_info = TimestampFieldInfo(_start_time),
        end_timestamp_field_info = TimestampFieldInfo(_end_time),
        has_video = False,
        has_audio = False,
        has_image = False
    )

    return card_info


def extract_all_dialogues(subtitles_filepath: OptionalFilepath) -> list[DialogueInfo]:
    """
    extract_all_dialogues

    Returns all dialogues from f_path parsed.

    :param subtitles_filepath: Filepath of the subtitle file.
    :return: A list with the parsed dialogues into DialogueInfo objects,
             if no filepath was specified return an empty list.
    """

    list_dialogues: list[DialogueInfo] = []

    if not subtitles_filepath:
        return list_dialogues

    open_sub: list[Dialogue] | SubRipFile | None = open_sub_file(subtitles_filepath)

    if not open_sub:
        die("open_sub_file function call failed.")

    for sub in open_sub:
        list_dialogues.append(create_dialogue_info(split_dialogue_line(sub)))

    return list_dialogues


def set_widget_margin(
    widget: Widget,
    start: float,
    top: float | None = None,
    end: float | None = None,
    bottom: float | None = None
) -> None:
    """
    set_widget_margin

    Sets the margin for the widget.
    If only the start parameter is provided all the other margins will be set to the value of start.

    :param widget: Widget which the margin should be set.
    :param start: The start margin.
    :param top: The top margin.
    :param end: The end margin.
    :param bottom: The bottom margin.
    :returm:
    """

    if top == None and end == None and bottom == None:
        widget.set_margin_start(int(start))
        widget.set_margin_top(int(start))
        widget.set_margin_end(int(start))
        widget.set_margin_bottom(int(start))

        return

    widget.set_margin_start(int(start))

    if top != None: widget.set_margin_top(int(top))
    if end != None: widget.set_margin_end(int(end))
    if bottom != None: widget.set_margin_bottom(int(bottom))


def get_tagged_text_from_text_buffer(
    text_buffer: TextBuffer,
    format_tags: FormatTags = FormatTags.PANGO_MARKUP
) -> str:
    """
    get_tagged_text_from_text_buffer

    Gets the text from a Gtk.TextBuffer and also its tags in the specified format by format_tags.

    :param text_buffer: The Gtk.TextBuffer the pango markup should be extracted from.
    :param format_tags: Tell which format the tags should have, defaults to pango markup.
    :return: The text in pango markup style.
    """

    text_segment_iter: TextIter = text_buffer.get_start_iter()
    end_iter: TextIter = text_buffer.get_end_iter()
    tagged_text: str = ""

    while text_segment_iter.compare(end_iter) < 0:
        tags_segment_iter: TextIter = text_segment_iter.copy()
        tags: list[TextTag] = tags_segment_iter.get_tags()

        tags_segment_iter.forward_to_tag_toggle()

        text_segment: str = markup_escape_text(text_buffer.get_text(text_segment_iter, tags_segment_iter, False), length = -1)

        for tag in tags:
            tag_name: str = tag.get_property("name")
            foreground_gdk_rgba: GdkRGBA | None = tag.get_property("foreground_rgba")
            background_gdk_rgba: GdkRGBA | None = tag.get_property("background_rgba")
            foreground_rgba: RGBA | None = RGBA.create_from(foreground_gdk_rgba) if foreground_gdk_rgba else None
            background_rgba: RGBA | None = RGBA.create_from(background_gdk_rgba) if background_gdk_rgba else None

            if foreground_rgba and format_tags == FormatTags.PANGO_MARKUP:
                text_segment = f"<span foreground=\"{foreground_rgba.hex_16bits_channel_string}\">{text_segment}</span>"
            elif background_rgba and format_tags == FormatTags.PANGO_MARKUP:
                text_segment = f"<span background=\"{background_rgba.hex_16bits_channel_string}\">{text_segment}</span>"
            elif foreground_rgba:
                text_segment = f"<span style=\"color: {foreground_rgba.hex_16bits_channel_string};\">{text_segment}</span>"
            elif background_rgba:
                text_segment = (
                    f"<span style=\"background-color: {background_rgba.hex_16bits_channel_string};\">{text_segment}</span>"
                )
            else:
                text_segment = f"<{tag_name}>{text_segment}</{tag_name}>"

        tagged_text += text_segment
        text_segment_iter = tags_segment_iter

    return tagged_text


def apply_pango_markup_to_text_buffer(text_buffer: TextBuffer, pango_markup_text: str) -> None:
    """
    apply_pango_markup_to_text_buffer

    Inserts the text into the text buffer, applying any pango markup style attributes.

    :param text_buffer: The Gtk.TextBuffer the pango markup should be applied.
    :param pango_markup_text: The text in pango markup style.
    :return:
    """

    text_buffer.set_text("")

    text: str
    attribute_list: AttrList
    current_text_offset: int = 0
    end_attribute_offset: int = 0

    # FIXME: Right now this doesn't handle malformed markup attribute
    try:
        _, attribute_list, text, _ = parse_markup(pango_markup_text, -1, "\x00")
    except GLibError as e:
        _print(f"Error parsing markup: {e}" + NEW_LINE, True)
        return

    attribute_list_iter: AttrIterator = attribute_list.get_iterator()

    text_buffer.insert(text_buffer.get_start_iter(), text)

    while True:
        _, end_attribute_offset = attribute_list_iter.range()

        for attribute in attribute_list_iter.get_attrs():
            attribute_color: AttrColor | None = attribute.as_color()
            attr_int: AttrInt | None = attribute.as_int()
            attribute_int: int | None = attr_int.value if attr_int else None
            attribute_type: AttrType = attribute.klass.type
            tag_name: str | None = None

            if attribute_type == AttrType.WEIGHT and attribute_int == Weight.BOLD:
                tag_name = "b"
            elif attribute_type == AttrType.STYLE and attribute_int == Style.ITALIC:
                tag_name = "i"
            elif attribute_type == AttrType.UNDERLINE and attribute_int == Underline.SINGLE:
                tag_name = "u"
            elif attribute_type == AttrType.FOREGROUND and attribute_color:
                rgba: RGBA = RGBA()
                rgba.parse(attribute_color.color.to_string())
                tag_name = f"color: {rgba.hex_16bits_channel_string}"
            elif attribute_type == AttrType.BACKGROUND and attribute_color:
                rgba: RGBA = RGBA()
                rgba.parse(attribute_color.color.to_string())
                tag_name = f"background-color: {rgba.hex_16bits_channel_string}"
            if tag_name:
                text_buffer.apply_tag_by_name(
                    tag_name,
                    text_buffer.get_iter_at_offset(current_text_offset),
                    text_buffer.get_iter_at_offset(end_attribute_offset)
                )

        current_text_offset = end_attribute_offset

        if not attribute_list_iter.next(): break


def apply_tagged_text_to_text_buffer(text_buffer: TextBuffer, tagged_text: str) -> None:
    """
    apply_tagged_to_text_buffer

    Inserts the text into the buffer, applying any tags.

    :param text_buffer: The Gtk.TextBuffer the pango markup should be applied.
    :param tagged_text: The text with tags.
    :return:
    """

    text_buffer.set_text("")

    parser: TextBufferPangoMarkupParser = TextBufferPangoMarkupParser(text_buffer)
    parser.feed(tagged_text)


def create_cache_dir() -> None:
    """
    create_cache_dir

    Create the directory used to cache files used in the process making of Anki's cards.

    :return:
    """

    makedirs(CACHE_MEDIA_DIR, exist_ok=True)


def cache_recently_used_files(
    anki_collection_filepath: Filepath,
    video_filepath: Filepath,
    sub_filepath: Filepath,
    deck_name: str,
    optional_sub_filepath: OptionalFilepath = None,
    ) -> None:
    """
    cache_recently_used_files

    Writes the recently used collection, video, subs and deck name to a file.

    :param anki_collection_filepath: Path to the collection.anki2.
    :param video_filepath: Path to the video file.
    :param sub_filepath: Path to the subtitle file.
    :param deck_name: Name of the deck.
    :param optional_sub_filepath: Optional path to an optional subtitle file.
    :return:
    """

    data: str = "#! /usr/bin/env toml\n\n"

    if not path.commonpath([CACHE_MEDIA_DIR, anki_collection_filepath]) == CACHE_MEDIA_DIR:
        data += f"anki_collection_filepath = \"{anki_collection_filepath}\"\n"
    else:
        data += f"anki_collection_filepath = \"\"\n"

    if not path.commonpath([CACHE_MEDIA_DIR, video_filepath]) == CACHE_MEDIA_DIR:
        data += f"video_filepath = \"{video_filepath}\"\n"
    else:
        data += f"video_filepath = \"\"\n"

    if not path.commonpath([CACHE_MEDIA_DIR, sub_filepath]) == CACHE_MEDIA_DIR:
        data += f"subtitles_filepath = \"{sub_filepath}\"\n"
    else:
        data += f"subtitles_filepath = \"\"\n"

    if optional_sub_filepath and not path.commonpath([CACHE_MEDIA_DIR, optional_sub_filepath]) == CACHE_MEDIA_DIR:
        data += f"optional_subtitles_filepath = \"{optional_sub_filepath}\"\n" \
            if optional_sub_filepath \
            else "optional_subtitles_filepath = \"\"\n"

    data += f"deck_name = \"{deck_name}\"\n"

    with open(RECENTLY_USED_FILEPATH, "w+") as f:
        f.write(data)


def get_recently_used_files() -> dict[str, str] | None:
    """
    get_recently_used_files

    Parses the toml file to get the recently used files.

    :return: A dictionary structure with the recently used filepaths.
    """

    with open(RECENTLY_USED_FILEPATH, "rb") as fp:
        data: dict[str, str] | None = handle_exception_if_any(
            f"Failed to parse file: {RECENTLY_USED_FILEPATH}.\n" \
            "Probably there's something wrong with the this toml file",
            False,
            load,
            fp
        )

    return data


def timestamp_to_timedelta(timestamp: str,  _format: str = "%H:%M:%S.%f") -> timedelta:
    """
    timestamp_to_timedelta

    Return a timedelta object built based by the timestamp.

    :param timestamp: Timestamp in the format of _format.
    :param _format: Format of the timestamps.
    :return: timedelta object.
    """

    parsed_time: datetime = datetime.strptime(timestamp, _format)

    return timedelta(
        hours=parsed_time.hour,
        minutes=parsed_time.minute,
        seconds=parsed_time.second,
        microseconds=parsed_time.microsecond // 1000
    )


def is_timestamp_within(
    start_timestamp: str,
    end_timestamp: str,
    given_timestamp: str,
    _format: str = "%H:%M:%S.%f"
) -> bool:
    """
    is_timestamp_within

    Tell if the given timestamp is within the start and end timestamp.

    :param start_timestamp: Start timestamp in the format of _format.
    :param end_timestamp: End timestamp in the format of _format.
    :param given_timestamp: Given timestamp in the format of _format.
    :param _format: Format of the timestamps.
    :return: True if the given time is within the start and end timestamp.
    """

    start_timedelta: timedelta = timestamp_to_timedelta(start_timestamp, _format)
    end_timedelta: timedelta = timestamp_to_timedelta(end_timestamp, _format)
    given_timedelta: timedelta = timestamp_to_timedelta(given_timestamp, _format)

    return start_timedelta <= given_timedelta <= end_timedelta


def get_available_encoded_languages(video_filepath: str) -> dict[str, dict[str, str]]:
    """
    Return a dictionary of available languages, if there's any.

    :param video_filepath: Path to the video file.
    :return: Available languages.
    """

    languages: dict[str, dict[str, str]] = {}

    try:
        streams: list[dict[str, Any]] | None = probe(
            video_filepath,
            select_streams = "s",
            show_entries = "stream=index,codec_name,codec_type:stream_tags=language",
            loglevel = "quiet"
        ).get("streams")

        if not streams:
            return languages

        for stream in streams:
            index: str | None = stream.get("index")
            codec_name: str | None = stream.get("codec_name")
            codec_type: str | None = stream.get("codec_type")
            tags: dict[str, str] | None = stream.get("tags")

            if not codec_name or not tags or codec_type != "subtitle" or not index:
                continue

            language: str | None = tags.get("language")

            if not language:
                continue

            languages[language + " - " + str(index)] = {"index": str(index), "language": language, "codec_name": codec_name}
    except FFMPEGError as e:
        _print(f"Error running ffmpeg probe: {e.stderr.decode()}", True)

    return languages


def write_subtitle_file(video_filepath: Filepath, stream_index: str, language: str, codec_name: str) -> Filepath | None:
    """
    write_subtitle_file

    Writes the selected language subtitles to a file.

    :param video_filepath: Video filepath.
    :param stream_index: Selected language index.
    :param language: Selected language.
    :param codec_name: Name of the codec used in the encoded subtitle.
    :return: The filepath on success writing the file, None otherwise.
    """

    output_filepath: Filepath
    basename, _ = path.splitext(path.basename(video_filepath))
    output_filepath = path.join(CACHE_MEDIA_DIR, basename + "-" + language + "." + codec_name)

    try:
        FFMPEGInput(video_filepath).output(
            output_filepath,
            map=f"0:{stream_index}"
        ).global_args(
            "-y",
            "-nostdin",
            "-loglevel",
            "quiet"
        ).run()
    except FFMPEGError as e:
        _print(f"Error running ffmpeg to write subtitle file: {e.stderr.decode()}", True)

    return output_filepath if path.exists(output_filepath) else None


__all__: list[str] = [
    "remove_cached_media_files", "create_cache_dir", "cut_video", "extract_all_dialogues",
    "get_tagged_text_from_text_buffer", "apply_pango_markup_to_text_buffer",
    "apply_tagged_text_to_text_buffer", "is_file_collection",
    "is_file_subtitles", "is_file_video", "cache_recently_used_files",
    "set_widget_margin", "handle_exception_if_any", "get_recently_used_files",
    "get_available_encoded_languages", "write_subtitle_file"
]

