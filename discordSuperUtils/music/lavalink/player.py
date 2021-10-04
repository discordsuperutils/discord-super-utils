import wavelink

from .equalizer import Equalizer


class LavalinkPlayer(wavelink.Player):
    def __init__(self, *args, **kwargs):
        print(args, kwargs)
        super().__init__(*args, **kwargs)

    async def set_eq(self, equalizer: Equalizer) -> None:
        await self.node._websocket.send(
            op="filters", guildId=str(self.guild.id), bands=equalizer.eq
        )
        self._equalizer = equalizer
