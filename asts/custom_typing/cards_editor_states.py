from enum import IntEnum


class CardsEditorStates(IntEnum):
    NORMAL      = 0
    RUNNING     = 2
    CANCELLED   = 3


class CardsEditorState:
    def __init__(self):
        """
        CardsEditorState

        Simple class to keep track of the cards editor window.
        NORMAL: The window is open for editing the cards normally.
        RUNNING: The medias are being generated and the cards are being
                 written to the Anki's database.
        CANCELLED: The user issued a cancel operation where the running
                   state should be stopped.

        :return:
        """

        self._state: CardsEditorStates = CardsEditorStates.NORMAL


    def get_state(self) -> CardsEditorStates:
        """
        state

        Property state getter.

        :return: State.
        """

        return self._state


    def set_state(self, state: CardsEditorStates) -> None:
        """
        state

        Property state setter.

        :param state: The new state.

        :return:
        """

        if self._state == CardsEditorStates.NORMAL and state == CardsEditorStates.CANCELLED: return
        if self._state == CardsEditorStates.CANCELLED and state == CardsEditorStates.RUNNING: return

        self._state = state


    def is_state(self, state: CardsEditorStates) -> bool:
        """
        is_state

        Tells whether the currently set state is the same as other state.

        :param state: The state that should be checked against with.
        :return: True if the state is the same as the currently set state.
        """

        return (self._state == state)


__all__: list[str] = ["CardsEditorStates", "CardsEditorState"]

