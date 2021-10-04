from __future__ import annotations

from typing import List

__all__ = ("Equalizer",)


class Equalizer:
    """
    Represents a Equalizer that supports different voice effects.
    """

    __slots__ = ("eq", "raw", "name")

    def __init__(self, *, levels: List[float], name: str = "CustomEqualizer"):
        self.eq = [{"band": index, "gain": gain} for index, gain in enumerate(levels)]
        self.raw = levels

        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Equalizer name={self.name}, raw={self.eq}>"

    @classmethod
    def flat(cls) -> Equalizer:
        levels = [0.0 for i in range(15)]

        return cls(levels=levels, name="Flat")

    @classmethod
    def boost(cls):
        levels = [
            0.08,
            0.12,
            0.2,
            0.18,
            0.15,
            0.1,
            0.05,
            0.0,
            0.02,
            -0.04,
            -0.06,
            -0.08,
            -0.10,
            -0.12,
            -0.14,
        ]

        return cls(levels=levels, name="Boost")

    @classmethod
    def metal(cls):
        levels = [
            0.0,
            0.1,
            0.1,
            0.15,
            0.13,
            0.1,
            0.0,
            0.125,
            0.175,
            0.175,
            0.125,
            0.125,
            0.1,
            0.075,
            0.0,
        ]

        return cls(levels=levels, name="Metal")

    @classmethod
    def piano(cls):
        levels = [
            -0.25,
            -0.25,
            -0.125,
            0.0,
            0.25,
            0.25,
            0.0,
            -0.25,
            -0.25,
            0.0,
            0.0,
            0.5,
            0.25,
            -0.025,
        ]

        return cls(levels=levels, name="Piano")
