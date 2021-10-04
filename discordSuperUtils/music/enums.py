from enum import Enum


__all__ = ("Loops", "PlaylistType", "ManagerType")


class Loops(Enum):
    NO_LOOP = 0
    LOOP = 1
    QUEUE_LOOP = 2


class PlaylistType(Enum):
    SPOTIFY = 0
    YOUTUBE = 1


class ManagerType(Enum):
    FFMPEG = 0
    LAVALINK = 1
