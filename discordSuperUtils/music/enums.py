from enum import Enum


__all__ = ("Loops",)


class Loops(Enum):
    NO_LOOP = 0
    LOOP = 1
    QUEUE_LOOP = 2
