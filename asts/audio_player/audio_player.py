from asts.custom_typing.globals import GST_VERSION, GLIB_VERSION

from gi import require_version
require_version(*GST_VERSION)
require_version(*GLIB_VERSION)

from gi.repository import Gst
from gi.repository.GObject import GObject, SignalFlags, GType
from gi.repository.GLib import Error
from gi.repository.Gst import (
    Element, Bus, Message, StateChangeReturn,
    State, SECOND
)

from os import path
from typing import cast, Any, Sequence

from asts.utils.core_utils import die, _print
from asts.custom_typing.aliases import Filepath


class AudioPlayer(GObject):
    __gsignals__: dict[str, tuple[SignalFlags, Any, Sequence[type | GType ]]] = {
        "started": (SignalFlags.RUN_FIRST, None, ()),
        "stopped": (SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self):
        """
        AudioPlayer

        A simple GStreamer audio player with play/pause/stop functionality.
        """

        super().__init__()

        if not Gst.is_initialized():
            Gst.init()

        player: Element | None = Gst.ElementFactory.make("playbin", "player")

        if not player:
            die("Failed to create a playbin Gst.Element.")

        self._player: Element = player
        self._bus: Bus = cast(Bus, self._player.get_bus())

        self._bus.add_signal_watch()
        self._bus.connect("message::state-changed", self._on_state_changed)
        self._bus.connect("message::eos", self._on_eos)
        self._bus.connect("message::error", self._on_error)


    def _on_eos(self, _: Bus, __: Message) -> None:
        """
        _on_eos

        Handles the EOS incoming message from the GStreamer bus.

        Stops the pipeline when an End-Of-Stream (EOS).

        :param bus: GStreamer bus which emitted the message.
        :param message: Incoming GStreamer message to process.
        :return:
        """

        self.stop()


    def _on_state_changed(self, _: Bus, message: Message) -> None:
        """
        _on_state_changed

        Handles the state-changed incoming message from the GStreamer bus.
        Emits the signal 'started' on State.Playing state, and 'stopped' on State.NULL state.

        :param bus: GStreamer bus which emitted the message.
        :param message: Incoming GStreamer message to process.
        :return:
        """

        if message.src != self._player:
            return

        old_state: State
        current_state: State

        (old_state, current_state, __) = message.parse_state_changed()

        if current_state == State.PLAYING and old_state != State.PLAYING:
            self.emit("started")


    def _on_error(self, _: Bus, message: Message) -> None:
        """
        _on_message_bus

        Handles the error incoming message from the GStreamer bus.

        Stops the pipeline when an ERROR message is received.

        :param bus: GStreamer bus which emitted the message.
        :param message: Incoming GStreamer message to process.
        :return:
        """

        error: Error
        debug: str
        error, debug = message.parse_error()

        _print(f"GStreamer error: {error}, {debug}", error=True)
        self.stop()


    def play(self, filepath: Filepath) -> None:
        """
        play

        Starts playback of the given media file.

        Resets the current player state, sets the media URI,
        and changes the player state to PLAYING.

        :param filepath: Path to the media file to play.
        :return:
        """

        uri: Filepath = f"file://{path.abspath(filepath)}"

        self._player.set_state(State.NULL)
        self._player.set_property("uri", uri)
        self._player.set_state(State.PLAYING)


    def pause(self) -> None:
        """
        pause

        Pauses the current media playback.

        Changes the player state to PAUSED.

        :return:
        """

        self._player.set_state(State.PAUSED)


    def stop(self) -> None:
        """
        stop

        Stops the current media playback.

        Resets the player state to NULL.

        :return:
        """

        self._player.set_state(State.NULL)
        self.emit("stopped")


    def is_playing(self) -> bool:
        """
        is_playing

        Checks whether the player is currently playing media.

        :return: True if the player state is PLAYING, otherwise False.
        """

        change_return: StateChangeReturn
        current_state: State

        (change_return, current_state, _) = self._player.get_state(0)

        if not change_return == StateChangeReturn.SUCCESS:
            current_state = self._player.get_state(SECOND * 5)[1]

        return  current_state == State.PLAYING


    def is_paused(self) -> bool:
        """
        is_playing

        Checks whether the player is currently playing media.

        :return: True if the player state is PLAYING, otherwise False.
        """

        change_return: StateChangeReturn
        current_state: State

        (change_return, current_state, _) = self._player.get_state(0)

        if not change_return == StateChangeReturn.SUCCESS:
            current_state = self._player.get_state(SECOND * 5)[1]

        return current_state == State.PAUSED


    def is_stopped(self) -> bool:
        """
        is_stopped

        Checks whether the player is currently stopped.

        Returns True when the player state is either
        NULL or READY.

        :return: True if the player is stopped, otherwise False.
        """

        change_return: StateChangeReturn
        current_state: State

        (change_return, current_state, _) = self._player.get_state(0)

        if not change_return == StateChangeReturn.SUCCESS:
            current_state = self._player.get_state(SECOND * 5)[1]

        return current_state in (State.NULL, State.READY)


__all__: list[str] = ["AudioPlayer"]
