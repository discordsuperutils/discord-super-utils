from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

__all__ = ("Equalizer",)


@dataclass
class Equalizer:
    """
    Represents an Equalizer that supports different voice effects.
    """

    raw: List[float]
    name: str

    @property
    def eq(self) -> List[Dict[str, Any]]:
        return [{"band": index, "gain": gain} for index, gain in enumerate(self.raw)]

    @classmethod
    def flat(cls) -> Equalizer:
        levels = [0.0 for i in range(15)]

        return cls(levels, "Flat")

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

        return cls(levels, "Boost")

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

        return cls(levels, "Metal")

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

        return cls(levels, "Piano")
    
    @classmethod
    def jazz(cls):
        levels = [
            -0.13,
            -0.11,
            -0.1,
            -0.1,
            0.14,
            0.2,
            -0.18,
            0.0,
            0.24,
            0.22,
            0.2,
            0.0,
            0.0,
            0.0,
            0.0,
        ]

        return cls(levels, "Jazz")


    @classmethod
    def pop(cls):
        levels = [
            -0.02,
            -0.01,
            0.08,
            0.1,
            0.15,
            0.1,
            0.03,
            -0.02,
            -0.035,
            -0.05,
            -0.05,
            -0.05,
            -0.05,
            -0.05,
            -0.05,
        ]

        return cls(levels, "Pop")

    @classmethod
    def treble(cls):
        levels = [
            -0.1, 
            -0.12, 
            -0.12, 
            -0.12, 
            -0.08, 
            -0.04, 
            0.0, 
            0.3, 
            0.34, 
            0.4, 
            0.35, 
            0.3, 
            0.3, 
            0.3, 
            0.3,
        ]

        return cls(levels, "Treble")
