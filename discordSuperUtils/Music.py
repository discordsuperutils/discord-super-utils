from __future__ import annotations

import asyncio
import re
import time
from enum import Enum
from typing import (
    Optional,
    TYPE_CHECKING,
    Iterable,
    List,
    Union,
    Any
)

import aiohttp
import discord
import youtube_dl

from .Base import EventManager
from .Spotify import SpotifyClient

if TYPE_CHECKING:
    from discord.ext import commands

__all__ = (
    "NotPlaying",
    "AlreadyPlaying",
    "NotConnected",
    "NotPaused",
    "QueueEmpty",
    "AlreadyConnected",
    "AlreadyPaused",
    "QueueError",
    "SkipError",
    "UserNotConnected",
    "InvalidSkipIndex",
    "Loops",
    "Player",
    "QueueManager",
    "MusicManager"
)


class NotPlaying(Exception):
    """Raises error when client is not playing"""


class AlreadyPlaying(Exception):
    """Raises error when player is already playing"""


class NotConnected(Exception):
    """Raises error when client is not connected to a voice channel"""


class NotPaused(Exception):
    """Raises error when player is not paused"""


class QueueEmpty(Exception):
    """Raises error when queue is empty"""


class AlreadyConnected(Exception):
    """Raises error when client is already connected to voice"""


class AlreadyPaused(Exception):
    """Raises error when player is already paused."""


class QueueError(Exception):
    """Raises error when something is wrong with the queue"""


class SkipError(Exception):
    """Raises error when there is no song to skip to"""


class UserNotConnected(Exception):
    """Raises error when user is not connected to channel"""


class InvalidSkipIndex(Exception):
    """Raises error when the skip index is < 0"""


class Loops(Enum):
    NO_LOOP = 0
    LOOP = 1
    QUEUE_LOOP = 2


class Player(discord.PCMVolumeTransformer):
    """
    Represents a music player.
    """

    __slots__ = ("data", "title", "stream_url", "url", "start_timestamp", "last_pause_timestamp", "duration")

    def __init__(self, source, *, data, volume=0.1):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.stream_url = data.get('url')
        self.url = data.get('webpage_url')

        self.start_timestamp = 0
        self.last_pause_timestamp = 0

        self.duration = data.get('duration') if data.get('duration') != 0 else "LIVE"

    def __str__(self):
        return self.title

    @staticmethod
    async def make_multiple_players(songs: Iterable[str]) -> List[Player]:
        """
        |coro|

        Returns a list of players from a iterable of queries.

        :param songs: The queries.
        :type songs: Iterable[str]
        :return: The list of created players.
        :rtype: List[Player]
        """

        tasks = [Player.make_player(song, playlist=False) for song in songs]
        return [x[0] for x in await asyncio.gather(*tasks) if x]

    @classmethod
    async def make_player(cls, query: str, playlist: bool = True) -> List[Player]:
        """
        |coro|

        Returns a list of players from the query.
        The list will contain the first video incase it is not a playlist.

        :param query: The query.
        :type query: str
        :param playlist: A bool indicating if the function should fetch playlists or get the first video.
        :type playlist: bool
        :return: The list of created players.
        :rtype: List[Player]
        """

        data = await MusicManager.fetch_data(query)
        if data is None:
            return []

        if 'entries' in data:
            if not playlist:
                data = data['entries'][0]
            else:
                return [cls(
                    discord.FFmpegPCMAudio(player['url'],
                                           **MusicManager.FFMPEG_OPTIONS), data=player) for player in data['entries']]

        filename = data['url']
        return [cls(discord.FFmpegPCMAudio(filename, **MusicManager.FFMPEG_OPTIONS), data=data)]


class QueueManager:
    __slots__ = ("queue", "volume", "history", "loop", "now_playing")

    def __init__(self, volume: float, queue: List[Player]):
        self.queue = queue
        self.volume = volume
        self.history = []
        self.loop = Loops.NO_LOOP
        self.now_playing = None

    def add(self, player: Player) -> None:
        """
        Adds a player to the queue.

        :param player: The player to add.
        :type player: Player
        :return: None
        :rtype: None
        """

        self.queue.append(player)

    def clear(self) -> None:
        """
        Clears the queue.

        :return: None
        :rtype: None
        """

        self.queue.clear()

    def remove(self, index: int) -> Union[Player, Any]:
        """
        Removes and element from the queue at the specified index, and returns the element's value.

        :param index: The index.
        :type index: int
        :return: The element's value
        :rtype: Union[Player, Any]
        """

        return self.queue.pop(index)


class MusicManager(EventManager):
    """
    Represents a MusicManager.
    """

    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    SPOTIFY_RE = re.compile("^https://open.spotify.com/")
    YTDL = youtube_dl.YoutubeDL({
        'format': 'bestaudio/best',
        'restrictfilenames': True,
        'noplaylist': False,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto'
    })

    __slots__ = ("bot", "client_id", "client_secret", "spotify_support", "inactivity_timeout", "queue", "spotify")

    def __init__(self, bot: commands.Bot, spotify_support: bool = True, inactivity_timeout: int = 60, **kwargs):
        super().__init__()
        self.bot = bot

        self.client_id = kwargs.get('client_id')
        self.client_secret = kwargs.get('client_secret')
        self.spotify_support = spotify_support
        self.inactivity_timeout = inactivity_timeout

        self.queue = {}

        if spotify_support:
            self.spotify = SpotifyClient(client_id=self.client_id, client_secret=self.client_secret)

    async def __ensure_activity(self, ctx: commands.Context) -> None:
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
            await ctx.voice_client.disconnect()
            await self.call_event("on_inactivity_disconnect", ctx)

    async def __check_connection(self,
                                 ctx: commands.Context,
                                 check_playing: bool = False,
                                 check_queue: bool = False) -> Optional[bool]:
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
            await self.call_event('on_music_error', ctx, NotConnected("Client is not connected to a voice channel"))
            return

        if check_playing and not ctx.voice_client.is_playing():
            await self.call_event('on_music_error', ctx, NotPlaying("Client is not playing anything currently"))
            return

        if check_queue and ctx.guild.id not in self.queue:
            await self.call_event('on_music_error', ctx, QueueEmpty("Queue is empty"))
            return

        return True

    async def __check_queue(self, ctx: commands.Context) -> None:
        """
        |coro|

        Plays the next song in the queue, handles looping and queue looping.

        :param ctx: The context of the voice client.
        :type ctx: commands.Contet
        :return: None
        :rtype: None
        """

        try:
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                return

            if self.queue[ctx.guild.id].loop == Loops.LOOP:
                song = self.queue[ctx.guild.id].now_playing
                player = (await Player.make_player(song.url, playlist=False))[0]

            elif self.queue[ctx.guild.id].loop == Loops.QUEUE_LOOP:
                song = self.queue[ctx.guild.id].remove(0)
                player = (await Player.make_player(song.url, playlist=False))[0]
                self.queue[ctx.guild.id].add(player)

            else:
                player = self.queue[ctx.guild.id].remove(0)

            self.queue[ctx.guild.id].now_playing = player

            if player is None or not ctx.voice_client:
                return

            player.volume = self.queue[ctx.guild.id].volume
            ctx.voice_client.play(player, after=lambda x: self.bot.loop.create_task(self.__check_queue(ctx)))
            player.start_timestamp = time.time()

            if self.queue[ctx.guild.id].loop == Loops.NO_LOOP:
                self.queue[ctx.guild.id].history.append(player)
                await self.call_event('on_play', ctx, player)

        except (IndexError, KeyError):
            if ctx.guild.id in self.queue:
                self.queue[ctx.guild.id].now_playing = None

            await self.call_event("on_queue_end", ctx)

    async def get_player_played_duration(self, ctx: commands.Context, player: Player) -> Optional[float]:
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
            start_timestamp = player.start_timestamp + time.time() - player.last_pause_timestamp

        time_played = time.time() - start_timestamp
        return min(time_played, time_played if player.duration == "LIVE" else player.duration)

    @staticmethod
    async def fetch_data(query: str) -> Optional[dict]:
        """
        |coro|

        Fetches the YTDL data of the query.

        :param query: The query.
        :type query: str
        :return: The YTDL data.
        :rtype: Optional[dict]
        """

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: MusicManager.YTDL.extract_info(query, download=False))
        except youtube_dl.utils.DownloadError:
            return None

    async def create_player(self, query: str) -> List[Player]:
        """
        |coro|

        Creates a list of players from the query.
        This function supports Spotify and all YTDL supported links.

        :param query: The query.
        :type query: str
        :return: The list of players.
        :rtype: List[Player]
        """

        if self.SPOTIFY_RE.match(query) and self.spotify_support:
            return await Player.make_multiple_players([song for song in await self.spotify.get_songs(query)])

        return await Player.make_player(query)

    async def queue_add(self, players: List[Player], ctx: commands.Context) -> None:
        """
        |coro|

        Adds a list of players to the ctx queue.
        If a queue does not exist in ctx, it creates one.

        :param players: The list of players.
        :type players: List[Player]
        :param ctx: The context.
        :type ctx: commands.Context
        :return: None
        :rtype: None
        """

        if not await self.__check_connection(ctx):
            return

        if ctx.guild.id in self.queue:
            self.queue[ctx.guild.id].queue += players
        else:
            self.queue[ctx.guild.id] = QueueManager(0.1, players)

    async def queue_remove(self, ctx: commands.Context, index: int) -> None:
        """
        |coro|

        Removes a player from the queue in ctx at the specified index.
        Calls on_music_error with QueueError if index is invalid.

        :param ctx: The context.
        :type ctx: commands.Context
        :param index: The index.
        :type index: int
        :return: None
        :rtype: None
        """

        if not await self.__check_connection(ctx, check_queue=True):
            return

        try:
            self.queue[ctx.guild.id].remove(index)
        except IndexError:
            await self.call_event('on_music_error', ctx, QueueError("Failure when removing player from queue"))

    async def lyrics(self, ctx: commands.Context, query: str = None) -> Optional[str]:
        """
        |coro|

        Returns the lyrics from the query or the currently playing song.

        :param ctx: The context.
        :type ctx: commands.Context
        :param query: The query.
        :type query: str
        :return: The lyrics.
        :rtype: Optional[str]
        """

        query = await self.now_playing(ctx) if query is None else query
        url = f"https://some-random-api.ml/lyrics?title={query}"

        async with aiohttp.ClientSession() as session:
            request = await session.get(url)
            request_json = await request.json()

            return request_json.get('lyrics', None)

    async def play(self, ctx: commands.Context, player: Player = None) -> Optional[bool]:
        """
        |coro|

        Plays the player or the next song in the queue if the player is not passed.

        :param ctx: The context.
        :type ctx: commands.Context
        :param player: The player.
        :type player: Player
        :return: A bool indicating if the play was successful
        :rtype: Optional[bool]
        """

        if not await self.__check_connection(ctx):
            return

        if player is not None:
            ctx.voice_client.play(player)
            return True

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
            await self.call_event('on_music_error', ctx, AlreadyPaused("Player is already paused."))
            return

        (await self.now_playing(ctx)).last_pause_timestamp = time.time()
        ctx.voice_client.pause()
        self.bot.loop.create_task(self.__ensure_activity(ctx))
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
            await self.call_event('on_music_error', ctx, NotPaused("Player is not paused"))
            return

        ctx.voice_client.resume()

        now_playing = await self.now_playing(ctx)
        now_playing.start_timestamp += time.time() - now_playing.last_pause_timestamp

        return True

    async def skip(self, ctx: commands.Context, index: int = None) -> Optional[Player]:
        """
        |coro|

        Skips to the index in ctx.
        Calls on_music_error with InvalidSkipIndex or SkipError.

        :param index: The index to skip to.
        :type index: int
        :param ctx: The context.
        :type ctx: commands.Context
        :return: A bool indicating if the skip was successful
        :rtype: Optional[Player]
        """

        if not await self.__check_connection(ctx, True, check_queue=True):
            return

        # Created duplicate to make sure InvalidSkipIndex isn't raised when the user does pass an index and the queue
        # is empty.
        skip_index = 0 if index is None else index - 1
        if not -1 < skip_index < len(self.queue[ctx.guild.id].queue):
            if index:
                await self.call_event('on_music_error', ctx, InvalidSkipIndex("Skip index invalid."))
                return

        if len(self.queue[ctx.guild.id].queue) <= skip_index:
            await self.call_event('on_music_error', ctx, SkipError("No song to skip to."))

        if skip_index > 0:
            removed_songs = self.queue[ctx.guild.id].queue[:skip_index]

            self.queue[ctx.guild.id].queue = self.queue[ctx.guild.id].queue[skip_index:]
            if self.queue[ctx.guild.id].loop == Loops.QUEUE_LOOP:
                self.queue[ctx.guild.id].queue += removed_songs

        player = self.queue[ctx.guild.id].queue[0]
        ctx.voice_client.stop()
        return player

    async def volume(self, ctx: commands.Context, volume: int = None) -> Optional[float]:
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

    async def join(self, ctx: commands.Context) -> Optional[bool]:
        """
        |coro|

        Joins the ctx voice channel.
        Calls on_music_error with AlreadyConnected or UserNotConnected.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: A bool indicating if the join was successful.
        :rtype: Optional[bool]
        """

        if ctx.voice_client and ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx,
                                  AlreadyConnected("Client is already connected to a voice channel"))
            return

        if not ctx.author.voice:
            await self.call_event('on_music_error', ctx, UserNotConnected("User is not connected to a voice channel"))
            return

        await ctx.author.voice.channel.connect()
        return True

    async def leave(self, ctx: commands.Context) -> Optional[bool]:
        """
        |coro|

        Leaves the voice channel in ctx.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: A bool indicating if the disconnection was successful.
        :rtype: Optional[bool]
        """

        if not await self.__check_connection(ctx):
            return

        await ctx.voice_client.disconnect()
        return True

    async def history(self, ctx: commands.Context) -> Optional[List[Player]]:
        """
        |coro|

        Returns a list of the played players.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: A list of played players.
        :rtype: Optional[List[Player]]
        """

        if not await self.__check_connection(ctx, check_queue=True):
            return

        return self.queue[ctx.guild.id].history

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
        if not now_playing and not ctx.voice_client.is_paused():
            await self.call_event('on_music_error', ctx, NotPlaying("Client is not playing anything currently"))

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

        self.queue[ctx.guild.id].loop = Loops.QUEUE_LOOP if self.queue[ctx.guild.id].loop != Loops.QUEUE_LOOP else \
            Loops.NO_LOOP

        if self.queue[ctx.guild.id].loop == Loops.QUEUE_LOOP:
            self.queue[ctx.guild.id].add(self.queue[ctx.guild.id].now_playing)

        return self.queue[ctx.guild.id].loop == Loops.QUEUE_LOOP

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

        self.queue[ctx.guild.id].loop = Loops.LOOP if self.queue[ctx.guild.id].loop != Loops.LOOP else Loops.NO_LOOP
        return self.queue[ctx.guild.id].loop == Loops.LOOP

    async def get_queue(self, ctx: commands.Context) -> Optional[List[Player]]:
        """
        |coro|

        Returns the queue of ctx.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: The queue.
        :rtype: Optional[List[Player]]
        """

        if not await self.__check_connection(ctx, check_queue=True):
            return

        return self.queue[ctx.guild.id].queue

    async def clear_queue(self, ctx: commands.Context) -> None:
        """
        |coro|

        Clears the ctx's guild's Queue

        :parameter ctx: Context object to fetch the guild from
        :type ctx: commands.Context
        :return: None
        :rtype: None
        """

        self.queue[ctx.guild.id].clear()
