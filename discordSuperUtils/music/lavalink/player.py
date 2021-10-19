from dataclasses import dataclass

import wavelink

from .equalizer import Equalizer


@dataclass(init=False)
class LavalinkPlayer(wavelink.Player):
    """
    Represents a LavalinkPlayer.
    """

    equalizer: Equalizer = Equalizer.flat()

    async def set_eq(self, equalizer: Equalizer) -> None:
        await self.node._websocket.send(
            op="equalizer", guildId=str(self.guild.id), bands=equalizer.eq
        )
        self.equalizer = equalizer
