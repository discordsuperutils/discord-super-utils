__all__ = (
    "NotPlaying",
    "NotConnected",
    "NotPaused",
    "QueueEmpty",
    "AlreadyConnected",
    "AlreadyPaused",
    "QueueError",
    "SkipError",
    "UserNotConnected",
    "InvalidSkipIndex",
    "InvalidPreviousIndex",
)


class NotPlaying(Exception):
    """Raises error when client is not playing"""


class NotConnected(Exception):
    """Raises error when client is not connected to a voice channel"""


class InvalidPreviousIndex(Exception):
    """Raises error when the previous index is < 0"""


class NotPaused(Exception):
    """Raises error when player is not paused"""


class QueueEmpty(Exception):
    """Raises error when queue is empty"""


class AlreadyConnected(Exception):
    """Raises error when client is already connected to voice"""


class AlreadyPaused(Exception):
    """Raises error when player is already paused."""


class QueueError(Exception):
    """Raises error when something is wrong with the queue"""


class SkipError(Exception):
    """Raises error when there is no song to skip to"""


class UserNotConnected(Exception):
    """Raises error when user is not connected to channel"""


class InvalidSkipIndex(Exception):
    """Raises error when the skip index is < 0"""
