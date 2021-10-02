from __future__ import annotations

import asyncio
import random
import re
import time
from typing import Optional, TYPE_CHECKING, List, Tuple, Dict, Union

import aiohttp
import discord

from .enums import Loops
from .exceptions import (
    QueueEmpty,
    NotPlaying,
    NotConnected,
    QueueError,
    AlreadyPaused,
    NotPaused,
    InvalidSkipIndex,
    SkipError,
    AlreadyConnected,
    UserNotConnected,
    InvalidPreviousIndex,
)
from .player import Player
from .playlist import YoutubePlaylist, SpotifyPlaylist
from .queue import QueueManager
from ..base import EventManager, create_task
from ..spotify import SpotifyClient
from ..youtube import YoutubeClient

if TYPE_CHECKING:
    from discord.ext import commands

__all__ = ("MusicManager",)

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}
SPOTIFY_RE = re.compile("^https://open.spotify.com/")


class MusicManager(EventManager):
    """
    Represents a MusicManager.
    """

    __slots__ = (
        "bot",
        "client_id",
        "client_secret",
        "spotify_support",
        "inactivity_timeout",
        "queue",
        "spotify",
    )

    def __init__(
        self,
        bot: commands.Bot,
        spotify_support: bool = True,
        inactivity_timeout: int = 60,
        minimum_users: int = 1,
        opus_players: bool = False,
        **kwargs,
    ):
        super().__init__()
        self.bot = bot
        self.bot.add_listener(self.__on_voice_state_update, "on_voice_state_update")

        self.client_id = kwargs.get("client_id")
        self.client_secret = kwargs.get("client_secret")
        self.default_volume = kwargs.get("default_volume") or 0.1
        self.executable = kwargs.get("executable") or "ffmpeg"
        self.spotify_support = spotify_support
        self.inactivity_timeout = 0 if not inactivity_timeout else inactivity_timeout
        self.minimum_users = minimum_users

        self.queue: Dict[int, QueueManager] = {}
        self.youtube = YoutubeClient(loop=self.bot.loop)
        self.opus_players = opus_players

        if not discord.opus.is_loaded():
            try:
                discord.opus._load_default()
            except OSError:
                raise RuntimeError("Could not load an opus lib.")

        if spotify_support:
            self.spotify = SpotifyClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                loop=self.bot.loop,
            )

    async def cleanup(
        self, voice_client: Optional[discord.VoiceClient], guild: discord.Guild
    ) -> None:
        """
        |coro|

        Cleans up after a guild.

        :param Optional[discord.VoiceClient] voice_client: The voice client.
        :param discord.Guild guild: The guild.
        :return: None
        :rtype: None
        """

        if voice_client:
            await voice_client.disconnect()

        if guild.id in self.queue:
            self.queue[guild.id].cleanup()
            del self.queue[guild.id]

    async def __on_voice_state_update(self, member, before, after):
        voice_client = member.guild.voice_client
        channel_change = before.channel != after.channel

        if member == self.bot.user and channel_change:
            await self.cleanup(voice_client, member.guild)

        elif voice_client and channel_change:
            voice_members = list(
                filter(lambda x: not x.bot, voice_client.channel.members)
            )

            if len(voice_members) < self.minimum_users:
                await asyncio.sleep(self.inactivity_timeout)

                await self.cleanup(voice_client, member.guild)

    async def ensure_activity(self, ctx: commands.Context) -> None:
        """
        |coro|

        Waits the inactivity timeout and ensures the voice client in ctx is playing a song.
        If no song is playing, it disconnects and calls the on_inactivity_timeout event.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: None
        :rtype: None
        """

        if self.inactivity_timeout is None:
            return

        await asyncio.sleep(self.inactivity_timeout)

        if not ctx.voice_client:
            return

        if ctx.voice_client.is_connected() and not ctx.voice_client.is_playing():
            await self.cleanup(ctx.voice_client, ctx.guild)

            await self.call_event("on_inactivity_disconnect", ctx)

    async def __check_connection(
        self,
        ctx: commands.Context,
        check_playing: bool = False,
        check_queue: bool = False,
    ) -> Optional[bool]:
        """
        |coro|

        Checks the connection state of the voice client in ctx.

        :param ctx: The context.
        :type ctx: commands.Context
        :param check_playing: A bool indicating if the function should check if a song is playing.
        :type check_playing: bool
        :param check_queue: A bool indicating if the function should check if a queue exists.
        :type check_queue: bool
        :return: True if all the checks passed.
        :rtype: bool
        """

        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.call_event(
                "on_music_error",
                ctx,
                NotConnected("Client is not connected to a voice channel"),
            )
            return

        if check_playing and not ctx.voice_client.is_playing():
            await self.call_event(
                "on_music_error",
                ctx,
                NotPlaying("Client is not playing anything currently"),
            )
            return

        if check_queue and ctx.guild.id not in self.queue:
            await self.call_event("on_music_error", ctx, QueueEmpty("Queue is empty"))
            return

        return True

    async def _get_next_player(self, queue: QueueManager) -> Player:
        """
        |coro|

        Returns the next player that should be played from the queue.

        :param QueueManager queue: The queue.
        :return: The player.
        :rtype: Player
        """

        if queue.loop != Loops.LOOP:
            queue.pos += 1

        if queue.loop == Loops.LOOP:
            player = queue.now_playing

        elif queue.loop == Loops.QUEUE_LOOP:
            if queue.is_finished():
                queue.pos = queue.queue_loop_start

            player = queue.queue[
                random.randint(queue.pos, len(queue.queue) - queue.pos)
                if queue.shuffle
                else queue.pos
            ]

        else:
            if not queue.queue and queue.autoplay:
                last_video_id = queue.played_history[-1].data["videoDetails"]["videoId"]
                player = (await Player.get_similar_videos(last_video_id, self.youtube))[
                    0
                ]

            else:
                player = queue.queue[
                    random.randint(queue.pos, len(queue.queue) - queue.pos)
                    if queue.shuffle
                    else queue.pos
                ]

        return player

    async def __check_queue(self, ctx: commands.Context) -> None:
        """
        |coro|

        Plays the next song in the queue, handles looping, queue looping, autoplay, etc.

        :param ctx: The context of the voice client.
        :type ctx: commands.Context
        :return: None
        :rtype: None
        """

        try:
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                return

            queue = self.queue[ctx.guild.id]
            player = await self._get_next_player(queue)

            if player is None:
                await self.cleanup(None, ctx.guild)
                await self.call_event("on_queue_end", ctx)

            player.source = (
                discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(
                        player.stream_url, **FFMPEG_OPTIONS, executable=self.executable
                    ),
                    queue.volume,
                )
                if not self.opus_players
                else discord.FFmpegOpusAudio(
                    player.stream_url, **FFMPEG_OPTIONS, executable=self.executable
                )
            )

            ctx.voice_client.play(
                player.source,
                after=lambda x: create_task(self.bot.loop, self.__check_queue(ctx)),
            )
            player.start_timestamp = time.time()

            queue.played_history.append(player)
            queue.vote_skips = []
            if queue.loop == Loops.QUEUE_LOOP or queue.loop == Loops.NO_LOOP:
                await self.call_event("on_play", ctx, player)

        except (IndexError, KeyError):
            await self.cleanup(None, ctx.guild)
            await self.call_event("on_queue_end", ctx)

    async def get_playlist(
        self, player: Player
    ) -> Union[YoutubePlaylist, SpotifyPlaylist]:
        if SPOTIFY_RE.match(player.used_query) and self.spotify_support:
            spotify_info = await self.spotify.fetch_full_playlist(player.used_query)
            return SpotifyPlaylist.from_dict(spotify_info) if spotify_info else None

        playlist_info = await self.youtube.get_playlist_information(
            await self.youtube.get_query_id(player.used_query)
        )
        return YoutubePlaylist.from_dict(playlist_info) if playlist_info else None

    async def get_player_played_duration(
        self, ctx: commands.Context, player: Player
    ) -> Optional[float]:
        """
        |coro|

        Returns the played duration of a player.

        :param ctx: The context.
        :type ctx: commands.Context
        :param player: The player.
        :type player: Player
        :return: The played duration of the player in seconds.
        :rtype: Optional[float]
        """

        if not await self.__check_connection(ctx):
            return

        start_timestamp = player.start_timestamp
        if ctx.voice_client.is_paused():
            start_timestamp = (
                player.start_timestamp + time.time() - player.last_pause_timestamp
            )

        time_played = time.time() - start_timestamp
        return min(
            time_played, time_played if player.duration == "LIVE" else player.duration
        )

    async def create_player(
        self, query: str, requester: discord.Member
    ) -> List[Player]:
        """
        |coro|

        Creates a list of players from the query.
        This function supports Spotify and all YTDL supported links.

        :param requester: The requester.
        :type requester: discord.Member
        :param query: The query.
        :type query: str
        :return: The list of players.
        :rtype: List[Player]
        """

        if SPOTIFY_RE.match(query) and self.spotify_support:
            return await Player.make_multiple_players(
                self.youtube,
                query,
                [song for song in await self.spotify.get_songs(query)],
                requester,
            )

        return await Player.make_players(self.youtube, query, requester)

    async def queue_add(
        self, players: List[Player], ctx: commands.Context
    ) -> Optional[bool]:
        """
        |coro|

        Adds a list of players to the ctx queue.
        If a queue does not exist in ctx, it creates one.

        :param players: The list of players.
        :type players: List[Player]
        :param ctx: The context.
        :type ctx: commands.Context
        :return: A bool indicating if it was successful
        :rtype: Optional[bool]
        """

        if not await self.__check_connection(ctx):
            return

        if ctx.guild.id in self.queue:
            self.queue[ctx.guild.id].queue += players
        else:
            self.queue[ctx.guild.id] = QueueManager(self.default_volume, players)

        return True

    async def queue_remove(self, ctx: commands.Context, index: int) -> Optional[Player]:
        """
        |coro|

        Removes a player from the queue in ctx at the specified index.
        Calls on_music_error with QueueError if index is invalid.

        :param ctx: The context.
        :type ctx: commands.Context
        :param index: The index.
        :type index: int
        :return: The player that was removed, if applicable.
        :rtype: Optional[Player]
        """

        if not await self.__check_connection(ctx, check_queue=True):
            return

        try:
            queue = self.queue[ctx.guild.id]

            return queue.remove(queue.pos + index)
        except IndexError:
            await self.call_event(
                "on_music_error",
                ctx,
                QueueError("Failure when removing player from queue"),
            )

    async def lyrics(
        self, ctx: commands.Context, query: str = None
    ) -> Optional[Tuple[str, str, str]]:
        """
        |coro|

        Returns the lyrics from the query or the currently playing song.

        :param ctx: The context.
        :type ctx: commands.Context
        :param query: The query.
        :type query: str
        :return: The lyrics and the song name.
        :rtype: Optional[Tuple[str, str, str]]
        """

        query = await self.now_playing(ctx) if query is None else query
        if not query:
            return

        url = f"https://some-random-api.ml/lyrics?title={query}"

        async with aiohttp.ClientSession() as session:
            request = await session.get(url)
            request_json = await request.json(content_type=None)

            authors = request_json.get("author")
            title = request_json.get("title")
            lyrics = request_json.get("lyrics")

            return (title, authors, lyrics) if lyrics else None

    async def play(
        self,
        ctx: commands.Context,
    ) -> Optional[bool]:
        """
        |coro|

        Plays the player or the next song in the queue.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: A bool indicating if the play was successful
        :rtype: Optional[bool]
        """

        if not await self.__check_connection(ctx):
            return

        if not ctx.voice_client.is_playing():
            await self.__check_queue(ctx)
            return True

    async def pause(self, ctx: commands.Context) -> Optional[bool]:
        """
        |coro|

        Pauses the currently playing song in ctx.
        Calls on_music_error with AlreadyPaused if already paused.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: A bool indicating if the pause was successful
        :rtype: Optional[bool]
        """

        if not await self.__check_connection(ctx):
            return

        if ctx.voice_client.is_paused():
            await self.call_event(
                "on_music_error", ctx, AlreadyPaused("Player is already paused.")
            )
            return

        (await self.now_playing(ctx)).last_pause_timestamp = time.time()
        ctx.voice_client.pause()
        create_task(self.bot.loop, self.ensure_activity(ctx))
        return True

    async def resume(self, ctx: commands.Context) -> Optional[bool]:
        """
        |coro|

        Resumes the currently paused song in ctx.
        Calls on_music_error with NotPaused if not paused.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: A bool indicating if the resume was successful
        :rtype: Optional[bool]
        """

        if not await self.__check_connection(ctx):
            return

        if not ctx.voice_client.is_paused():
            await self.call_event(
                "on_music_error", ctx, NotPaused("Player is not paused")
            )
            return

        ctx.voice_client.resume()

        now_playing = await self.now_playing(ctx)
        now_playing.start_timestamp += time.time() - now_playing.last_pause_timestamp

        return True

    async def previous(
        self, ctx: commands.Context, index: int = None, no_autoplay: bool = False
    ) -> Optional[List[Player]]:
        """
        |coro|

        Plays the (index) player from the history.

        :param commands.Context ctx: The ctx.
        :param bool no_autoplay: A bool indicating if autoplayed songs should be added back to the queue.
        :param int index: The index.
        :return: The list of Players that have been added back.
        :rtype: Optional[List[Player]]
        """

        if not await self.__check_connection(ctx, True, check_queue=True):
            return

        queue = self.queue[ctx.guild.id]

        previous_index = 2 if index is None else index + 1
        if 0 >= previous_index:
            if index:
                await self.call_event(
                    "on_music_error",
                    ctx,
                    InvalidPreviousIndex("Previous index invalid."),
                )
                return

        original_queue_position = queue.pos
        queue.pos -= previous_index
        previous_players = queue.queue[queue.pos + 1 : original_queue_position]

        if no_autoplay:
            for player in previous_players[:]:
                if not player.requester:
                    previous_players.remove(player)
                    queue.queue.remove(player)

        ctx.voice_client.stop()
        return previous_players

    async def skip(self, ctx: commands.Context, index: int = None) -> Optional[Player]:
        """
        |coro|

        Skips to the index in ctx.
        Calls on_music_error with InvalidSkipIndex or SkipError.

        :param index: The index to skip to.
        :type index: int
        :param ctx: The context.
        :type ctx: commands.Context
        :return: The skiped player if applicable.
        :rtype: Optional[Player]
        """

        if not await self.__check_connection(ctx, True, check_queue=True):
            return

        queue = self.queue[ctx.guild.id]

        # Created duplicate to make sure InvalidSkipIndex isn't raised when the user does pass an index and the queue
        # is empty.
        skip_index = 0 if index is None else index - 1
        if not queue.pos < skip_index < len(queue.queue):
            if index:
                await self.call_event(
                    "on_music_error", ctx, InvalidSkipIndex("Skip index invalid.")
                )
                return

        if (
            not queue.autoplay
            and queue.loop != Loops.QUEUE_LOOP
            and (len(queue.queue) - 1) <= queue.pos + skip_index
        ):
            await self.call_event(
                "on_music_error", ctx, SkipError("No song to skip to.")
            )
            return

        original_position = queue.pos
        queue.pos += skip_index

        if queue.autoplay:
            last_video_id = queue.played_history[-1].data["videoDetails"]["videoId"]
            player = (await Player.get_similar_videos(last_video_id, self.youtube))[0]
            queue.add(player)
        else:
            player = queue.queue[original_position] if not queue.shuffle else None

        ctx.voice_client.stop()
        return player

    async def volume(
        self, ctx: commands.Context, volume: int = None
    ) -> Optional[float]:
        """
        |coro|

        Sets the volume in ctx.
        Returns the current volume if volume is None.

        :param volume: The volume to set.
        :type volume: int
        :param ctx: The context.
        :type ctx: commands.Context
        :return: The new volume.
        :rtype: Optional[float]
        """

        if not await self.__check_connection(ctx, True, check_queue=True):
            return

        if volume is None:
            return ctx.voice_client.source.volume * 100

        ctx.voice_client.source.volume = volume / 100
        self.queue[ctx.guild.id].volume = volume / 100
        return ctx.voice_client.source.volume * 100

    async def join(self, ctx: commands.Context) -> Optional[discord.VoiceChannel]:
        """
        |coro|

        Joins the ctx voice channel.
        Calls on_music_error with AlreadyConnected or UserNotConnected.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: The voice channel it joined.
        :rtype: Optional[discord.VoiceChannel]
        """

        if ctx.voice_client and ctx.voice_client.is_connected():
            await self.call_event(
                "on_music_error",
                ctx,
                AlreadyConnected("Client is already connected to a voice channel"),
            )
            return

        if not ctx.author.voice:
            await self.call_event(
                "on_music_error",
                ctx,
                UserNotConnected("User is not connected to a voice channel"),
            )
            return

        channel = ctx.author.voice.channel
        await channel.connect()
        return channel

    async def leave(self, ctx: commands.Context) -> Optional[discord.VoiceChannel]:
        """
        |coro|

        Leaves the voice channel in ctx.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: The voice channel it left.
        :rtype: Optional[discord.VoiceChannel]
        """

        if not await self.__check_connection(ctx):
            return

        if ctx.guild.id in self.queue:
            self.queue[ctx.guild.id].cleanup()
            del self.queue[ctx.guild.id]

        channel = ctx.voice_client.channel
        await ctx.voice_client.disconnect()
        return channel

    async def now_playing(self, ctx: commands.Context) -> Optional[Player]:
        """
        |coro|

        Returns the currently playing player.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: The currently playing player.
        :rtype: Optional[Player]
        """

        if not await self.__check_connection(ctx, check_queue=True):
            return

        now_playing = self.queue[ctx.guild.id].now_playing
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await self.call_event(
                "on_music_error",
                ctx,
                NotPlaying("Client is not playing anything currently"),
            )

        return now_playing

    async def queueloop(self, ctx: commands.Context) -> Optional[bool]:
        """
        |coro|

        Toggles the queue loop.

        :param ctx: The context
        :type ctx: commands.Context
        :return: A bool indicating if the queue loop is now enabled or disabled.
        :rtype: Optional[bool]
        """

        if not await self.__check_connection(ctx, check_playing=True, check_queue=True):
            return

        queue = self.queue[ctx.guild.id]

        queue.loop = (
            Loops.QUEUE_LOOP
            if self.queue[ctx.guild.id].loop != Loops.QUEUE_LOOP
            else Loops.NO_LOOP
        )

        if queue.loop == Loops.QUEUE_LOOP:
            queue.queue_loop_start = queue.pos

        return queue.loop == Loops.QUEUE_LOOP

    async def shuffle(self, ctx: commands.Context) -> Optional[bool]:
        """
        |coro|

        Toggles the shuffle feature.

        :param commands.Context ctx: The context
        :return: A bool indicating if the queue loop is now enabled or disabled.
        :rtype: Optional[bool]
        """

        if not await self.__check_connection(ctx, check_playing=True, check_queue=True):
            return

        self.queue[ctx.guild.id].shuffle = not self.queue[ctx.guild.id].shuffle
        return self.queue[ctx.guild.id].shuffle

    async def autoplay(self, ctx: commands.Context) -> Optional[bool]:
        """
        |coro|

        Toggles the autoplay feature.

        :param commands.Context ctx: The context
        :return: A bool indicating if autoplay is now enabled or disabled.
        :rtype: Optional[bool]
        """

        if not await self.__check_connection(ctx, check_playing=True, check_queue=True):
            return

        self.queue[ctx.guild.id].autoplay = not self.queue[ctx.guild.id].autoplay
        return self.queue[ctx.guild.id].autoplay

    async def loop(self, ctx: commands.Context) -> Optional[bool]:
        """
        |coro|

        Toggles the loop.

        :param ctx: The context
        :type ctx: commands.Context
        :return: A bool indicating if the loop is now enabled or disabled.
        :rtype: Optional[bool]
        """

        if not await self.__check_connection(ctx, check_playing=True, check_queue=True):
            return

        self.queue[ctx.guild.id].loop = (
            Loops.LOOP if self.queue[ctx.guild.id].loop != Loops.LOOP else Loops.NO_LOOP
        )
        return self.queue[ctx.guild.id].loop == Loops.LOOP

    async def get_queue(self, ctx: commands.Context) -> Optional[QueueManager]:
        """
        |coro|

        Returns the queue of ctx.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: The queue.
        :rtype: Optional[QueueManager]
        """

        if not await self.__check_connection(ctx, check_queue=True):
            return

        return self.queue[ctx.guild.id]
