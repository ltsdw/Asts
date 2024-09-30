from datetime   import datetime, timedelta
from typing     import Any, Callable, Iterable, TextIO, NoReturn, TypeVar
from sys        import exit, stdout, stderr
from platform   import system as ps
from itertools  import islice


# Plataform-wise new line character
NEW_LINE: str = "\n" if ps() != "Windows" else "\r\n"

def _print(msg: str, error: bool = False) -> None:
    """
    _print

    Print a message.

    :param msg: a string to be printed.
    :param error: if the error stream output should be used instead of the standard output.
    :return:
    """

    output: TextIO = stderr if error else stdout
    output.write(msg)
    output.flush()


def die(msg: str) -> NoReturn:
    """
    die

    Display a message of error and exit.

    :param msg: a string to be printed.
    :return:
    """

    _print(msg + NEW_LINE, True)
    exit(-1)


def handle_exception_if_any(
    message: str,
    fatal: bool,
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any
) -> Any:
    """
    handle_exception_if_any

    Calls the callable function and return its value, handling any exception that may be raised.

    :message: Message to be displayed in case of an exception is raised.
    :fatal: If it's True, the program will exit in case any exception is raised.
    :func: The callable function which may raise an exception.
    :args: Positional arguments to be passed to the callable function.
    :kwargs: Keyword arguments to be passed to the callable function.
    :return: If no exception is raised, the return value of the callable function is returned.
    """

    fatal_handler: Callable[[str], NoReturn | None] = die if fatal else _print

    try:
        return func(*args, **kwargs)
    except Exception as e:
        if not message:
            fatal_handler(message)

            return

        fatal_handler(f"{message}{NEW_LINE}{e}.")


def timestamp_to_timedelta(timestamp: str,  _format: str = "%H:%M:%S.%f") -> timedelta:
    """
    timestamp_to_timedelta

    Return a timedelta object built based by the timestamp.

    timestamp: Timestamp in the format of _format.
    _format: Format of the timestamps.
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

    start_timestamp: Start timestamp in the format of _format.
    end_timestamp: End timestamp in the format of _format.
    given_timestamp: Given timestamp in the format of _format.
    _format: Format of the timestamps.
    :return: True if the given time is within the start and end timestamp.
    """

    start_timedelta: timedelta = timestamp_to_timedelta(start_timestamp, _format)
    end_timedelta: timedelta = timestamp_to_timedelta(end_timestamp, _format)
    given_timedelta: timedelta = timestamp_to_timedelta(given_timestamp, _format)

    return start_timedelta <= given_timedelta <= end_timedelta


def clamp(value: float, _min: float, _max: float) -> float:
    """
    clamp

    Clamp floating number between two ranges.

    :param value: Value to be clamped.
    :param _min: Lower bound range value.
    :param _max: Upper bound range value.
    :return: Clamped value.
    """

    return _min if value < _min else _max if value > _max else value


_T = TypeVar("_T")

def get_chunked(_list: list[_T], chunk_size: int) -> list[list[_T]]:
    """
    get_chunked

    Create a list of lists where each internal list has size of chunk_size or less.

    :param _list: List that should be chunked.
    :param chunk_size: Number of items that each chunk should have.
    :return:
    """

    if chunk_size <= 0: return []

    _iter: Iterable[_T] = iter(_list)

    return [
        list(islice(_iter, chunk_size))
        for _ in range(0, len(_list), chunk_size)
    ]


__all__: list[str] = [
    "_print", "clamp", "die", "handle_exception_if_any",
    "is_timestamp_within", "get_chunked", "NEW_LINE"
]

