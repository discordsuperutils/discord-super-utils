from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Dict

import wavelink

from .equalizer import Equalizer
from ..enums import ManagerType
from ..music import MusicManager

if TYPE_CHECKING:
    from discord.ext import commands

__all__ = ("LavalinkMusicManager",)


class LavalinkMusicManager(MusicManager):
    """
    Represents a lavalink music manager.
    """

    def __init__(
        self,
        bot: commands.Bot,
        spotify_support: bool = True,
        inactivity_timeout: int = 60,
        minimum_users: int = 1,
        **kwargs,
    ):
        super().__init__(
            bot, spotify_support, inactivity_timeout, minimum_users, **kwargs
        )

        self.default_volume *= 100
        self.type = ManagerType.LAVALINK
        self.contexts: Dict[int, commands.Context] = {}
        self.bot.add_listener(self.__on_song_end, "on_wavelink_track_end")
        self.add_event(self.__on_queue_end, "on_queue_end")

    @staticmethod
    async def __on_queue_end(ctx):
        # MusicManager stops the voice client because the wavelink library assumes it is still playing.
        await ctx.voice_client.stop()

    async def __on_song_end(self, player: wavelink.Player, track, reason):
        await self._check_queue(self.contexts[player.guild.id])

    async def connect_node(
        self,
        host: str,
        password: str,
        port: int,
        identifier: str = "LavaLinkMusicManager",
    ) -> wavelink.Node:
        return await wavelink.NodePool.create_node(
            host=host, password=password, port=port, identifier=identifier, bot=self.bot
        )

    async def _check_queue(self, ctx: commands.Context) -> None:
        try:
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                return

            queue = self.queue[ctx.guild.id]
            player = await queue.get_next_player(self.youtube)

            if player is None:
                await self.cleanup(None, ctx.guild)
                await self.call_event("on_queue_end", ctx)

            await ctx.voice_client.set_volume(queue.volume)
            await ctx.voice_client.play(
                (await wavelink.YouTubeTrack.search(player.url))[0]
            )
            self.contexts[ctx.guild.id] = ctx

            queue.played_history.append(player)
            queue.vote_skips = []
            await self.call_event("on_play", ctx, player)

        except (IndexError, KeyError):
            await self.cleanup(None, ctx.guild)
            await self.call_event("on_queue_end", ctx)

    @MusicManager.ensure_connection()
    async def get_player_played_duration(
        self, ctx: commands.Context, _=None
    ) -> Optional[float]:
        return ctx.voice_client.position

    @MusicManager.ensure_connection(check_playing=True, check_queue=True)
    async def volume(
        self, ctx: commands.Context, volume: int = None
    ) -> Optional[float]:
        if volume is None:
            return ctx.voice_client.volume

        await ctx.voice_client.set_volume(volume)
        self.queue[ctx.guild.id].volume = volume
        return ctx.voice_client.volume

    @MusicManager.ensure_connection(check_playing=True)
    async def get_equalizer(self, ctx: commands.Context) -> Optional[Equalizer]:
        """
        Returns the ctx's equalizer.

        :param commands.Context ctx: The context.
        :return: The equalizer.
        :rtype: Optional[Equalizer]
        """

        return ctx.voice_client.equalizer or Equalizer.flat()

    @MusicManager.ensure_connection(check_playing=True)
    async def set_equalizer(self, ctx: commands.Context, equalizer: Equalizer) -> bool:
        """
        |coro|

        Sets the ctx's equalizer.

        :param commands.Context ctx: The context.
        :param Equalizer equalizer: The equalizer.
        :return: A bool indicating if the set was successful,
        :rtype: Optional[bool]
        """

        await ctx.voice_client.set_eq(equalizer)
        return True

    @MusicManager.ensure_connection(check_playing=True)
    async def seek(self, ctx: commands.Context, position: int = 0) -> Optional[bool]:
        """
        |coro|

        Seeks the current player to the position (ms)

        :param ctx: The context
        :param position: time to seek to (ms)
        :return: A bool indicating if the seek was successful
        :rtype: Optional[bool]
        """

        await ctx.voice_client.seek(position=position)
        return True
