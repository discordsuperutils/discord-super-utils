import wavelink

from .equalizer import Equalizer


class LavalinkPlayer(wavelink.Player):
    async def set_eq(self, equalizer: Equalizer) -> None:
        await self.node._websocket.send(
            op="filters", guildId=str(self.guild.id), bands=equalizer.eq
        )
        self._equalizer = equalizer
