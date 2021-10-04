import collections


class Equalizer:
    def __init__(self, *, levels: list, name: str = "CustomEqualizer"):
        self.eq = self._factory(levels)
        self.raw = levels

        self._name = name

    def __str__(self):
        return self._name

    def __repr__(self):
        return f"<Equalizer name={self._name}, raw={self.eq}>"

    @property
    def name(self):
        return self._name

    @staticmethod
    def _factory(levels: list):
        _dict = collections.defaultdict(int)

        _dict.update(levels)
        _dict = [{"band": i, "gain": _dict[i]} for i in range(15)]

        return _dict

    @classmethod
    def build(cls, *, levels: list, name: str = "CustomEqualizer"):
        """Build a custom Equalizer class with the provided levels.
        Parameters
        ------------
        levels: List[Tuple[int, float]]
            A list of tuple pairs containing a band int and gain float.
        name: str
            An Optional string to name this Equalizer. Defaults to 'CustomEqualizer'
        """
        return cls(levels=levels, name=name)

    @classmethod
    def flat(cls):
        levels = [
            (0, 0.0),
            (1, 0.0),
            (2, 0.0),
            (3, 0.0),
            (4, 0.0),
            (5, 0.0),
            (6, 0.0),
            (7, 0.0),
            (8, 0.0),
            (9, 0.0),
            (10, 0.0),
            (11, 0.0),
            (12, 0.0),
            (13, 0.0),
            (14, 0.0),
        ]

        return cls(levels=levels, name="Flat")

    @classmethod
    def boost(cls):
        levels = [
            (0, -0.075),
            (1, 0.125),
            (2, 0.125),
            (3, 0.1),
            (4, 0.1),
            (5, 0.05),
            (6, 0.075),
            (7, 0.0),
            (8, 0.0),
            (9, 0.0),
            (10, 0.0),
            (11, 0.0),
            (12, 0.125),
            (13, 0.15),
            (14, 0.05),
        ]

        return cls(levels=levels, name="Boost")

    @classmethod
    def metal(cls):
        levels = [
            (0, 0.0),
            (1, 0.1),
            (2, 0.1),
            (3, 0.15),
            (4, 0.13),
            (5, 0.1),
            (6, 0.0),
            (7, 0.125),
            (8, 0.175),
            (9, 0.175),
            (10, 0.125),
            (11, 0.125),
            (12, 0.1),
            (13, 0.075),
            (14, 0.0),
        ]

        return cls(levels=levels, name="Metal")

    @classmethod
    def piano(cls):
        levels = [
            (0, -0.25),
            (1, -0.25),
            (2, -0.125),
            (3, 0.0),
            (4, 0.25),
            (5, 0.25),
            (6, 0.0),
            (7, -0.25),
            (8, -0.25),
            (9, 0.0),
            (10, 0.0),
            (11, 0.5),
            (12, 0.25),
            (13, -0.025),
        ]

        return cls(levels=levels, name="Piano")
