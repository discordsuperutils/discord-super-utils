import wavelink

from .equalizer import Equalizer


class LavalinkPlayer(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.equalizer = None

    async def set_eq(self, equalizer: Equalizer) -> None:
        await self.node._websocket.send(
            op="equalizer", guildId=str(self.guild.id), bands=equalizer.eq
        )
        self.equalizer = equalizer
