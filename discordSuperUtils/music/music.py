from __future__ import annotations

import asyncio
import random
import time
import uuid
from typing import Optional, TYPE_CHECKING, List, Tuple, Dict, Callable, Union

import aiohttp
import discord

from .constants import *
from .enums import Loops, ManagerType
from .exceptions import (
    QueueEmpty,
    NotPlaying,
    NotConnected,
    RemoveIndexInvalid,
    AlreadyPaused,
    NotPaused,
    InvalidSkipIndex,
    SkipError,
    AlreadyConnected,
    UserNotConnected,
    InvalidPreviousIndex,
)
from .lavalink.player import LavalinkPlayer
from .player import Player
from .playlist import Playlist, UserPlaylist
from .queue import QueueManager
from .utils import get_playlist
from ..base import create_task, DatabaseChecker, maybe_coroutine
from ..spotify import SpotifyClient
from ..youtube import YoutubeClient

if TYPE_CHECKING:
    from discord.ext import commands

__all__ = ("MusicManager",)


class MusicManager(DatabaseChecker):
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
        super().__init__(
            [
                {
                    "user": "snowflake",
                    "playlist_url": "string",
                    "id": "string",
                }
            ],
            ["playlists"],
        )
        self.bot = bot
        self.bot.add_listener(self._on_voice_state_update, "on_voice_state_update")

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

        self._load_opus()

        if spotify_support:
            self.spotify = SpotifyClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                loop=self.bot.loop,
            )

        self.type = ManagerType.FFMPEG

    @staticmethod
    def _load_opus() -> None:
        """
        Ensures the opus library is loaded.

        :return: None
        :rtype: None
        :raises: RuntimeError: Could not find opus on the machine.
        """

        if not discord.opus.is_loaded():
            try:
                discord.opus._load_default()
            except OSError:
                raise RuntimeError("Could not find opus on the machine.")

    async def cleanup(
        self, voice_client: Optional[discord.VoiceClient], guild: discord.Guild
    ):
        """
        |coro|

        Cleans up after a guild.

        :param discord.Guild guild: The guild to cleanup.
        :param Optional[discord.VoiceClient] voice_client: The voice client.
        :return: None
        :rtype: None
        """

        if voice_client:
            try:
                await voice_client.disconnect(force=True)
            except ValueError:
                # Raised from wavelink
                pass

        if guild.id in self.queue:
            queue = self.queue.pop(guild.id)
            queue.cleanup()
            del queue

    @DatabaseChecker.uses_database
    async def add_playlist(
        self, user: discord.User, url: str
    ) -> Optional[UserPlaylist]:
        """
        |coro|

        Adds a playlist to the user's account.
        Saves the playlist in the database.

        :param discord.User user: The owner of the playlist.
        :param str url: The playlist URL.
        :return: None
        :rtype: None
        """

        playlist = await get_playlist(self.spotify, self.youtube, url)

        if not playlist:
            return

        generated_id = str(uuid.uuid4())
        await self.database.insertifnotexists(
            self.tables["playlists"],
            {"user": user.id, "playlist_url": url, "id": generated_id},
            {"user": user.id, "playlist_url": url},
        )

        return UserPlaylist(self, user, generated_id, playlist)

    @DatabaseChecker.uses_database
    async def get_playlist(
        self, user: discord.User, playlist_id: str, partial: bool = False
    ) -> Optional[UserPlaylist]:
        """
        |coro|

        Gets a user playlist by id.

        :param str playlist_id: The playlist id.
        :param bool partial: Indicating if the function should not fetch the playlist data.
        :param discord.User user: The user.
        :return: The user playlist.
        :rtype: Optional[UserPlaylist]
        """

        playlist = await self.database.select(
            self.tables["playlists"], [], {"user": user.id, "id": playlist_id}
        )

        if playlist:
            return UserPlaylist(
                self,
                user,
                playlist_id,
                await get_playlist(self.spotify, self.youtube, playlist["playlist_url"])
                if not partial
                else None,
            )

    @DatabaseChecker.uses_database
    async def get_user_playlists(
        self, user: discord.User, partial: bool = False
    ) -> List[UserPlaylist]:
        """
        |coro|

        Returns the user's playlists.

        :param discord.User user: The user.
        :param bool partial: Indicating if the function should not fetch the playlist data.
        :return: The list of user playlists.
        :rtype: List[UserPlaylist]
        """

        user_playlist_ids = await self.database.select(
            self.tables["playlists"], ["id"], {"user": user.id}, True
        )

        return list(
            await asyncio.gather(
                *[
                    self.get_playlist(user, user_playlist_id["id"], partial)
                    for user_playlist_id in user_playlist_ids
                ]
            )
        )

    async def _on_voice_state_update(self, member, before, after):
        voice_client = member.guild.voice_client
        channel_change = before.channel != after.channel

        if member == self.bot.user and channel_change and before.channel:
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

        if (
            ctx.voice_client
            and ctx.voice_client.is_connected()
            and not ctx.voice_client.is_playing()
        ):
            await self.cleanup(ctx.voice_client, ctx.guild)

            await self.call_event("on_inactivity_disconnect", ctx)

    async def _check_connection(
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

    def ensure_connection(*d_args, **d_kwargs) -> Callable:
        """
        A decorator which ensures there is a proper connection before invoking the decorated function.

        :param d_args: The connection arguments.
        :param d_kwargs: The connection key arguments.
        :return: The decorator.
        :rtype: Callable
        """

        def decorator(function):
            async def wrapper(self, ctx, *args, **kwargs):
                if await self._check_connection(ctx, *d_args, **d_kwargs):
                    return await function(self, ctx, *args, **kwargs)

            return wrapper

        return decorator

    async def _check_queue(self, ctx: commands.Context) -> None:
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
            player = await queue.get_next_player(self.youtube)

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
                after=lambda x: create_task(self.bot.loop, self._check_queue(ctx)),
            )

            player.start_timestamp = time.time()

            queue.played_history.append(player)
            queue.vote_skips = []
            await self.call_event("on_play", ctx, player)

        except (IndexError, KeyError):
            await self.cleanup(None, ctx.guild)
            await self.call_event("on_queue_end", ctx)

    async def get_player_playlist(self, player: Player) -> Optional[Playlist]:
        """
        |coro|

        Returns the player's playlist, if applicable.

        :param Player player: The player.
        :return: The player's playlist.
        :rtype: Optional[Playlist]
        """

        return await get_playlist(self.spotify, self.youtube, player.used_query)

    @ensure_connection()
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

        start_timestamp = player.start_timestamp
        if ctx.voice_client.is_paused():
            start_timestamp = (
                player.start_timestamp + time.time() - player.last_pause_timestamp
            )

        time_played = time.time() - start_timestamp
        return min(
            time_played, time_played if player.duration == "LIVE" else player.duration
        )

    async def create_playlist_players(
        self, playlist: Playlist, requester: discord.Member
    ) -> List[Player]:
        """
        |coro|

        Returns a list of players from the playlist.

        :param Playlist playlist: The playlist.
        :param discord.Member requester: The requester.
        :return: The list of created players.
        :rtype: List[Player]
        """

        return await Player.make_multiple_players(
            self.youtube,
            playlist.url,
            [
                str(song) for song in playlist.songs
            ],  # Converts the song to str to convert any spotify tracks.
            requester,
        )

    @staticmethod
    async def fetch_ytdl_data(url: str) -> Optional[dict]:
        """
        |coro|

        Fetches the data from a url.

        :param str url: The url to fetch the data from.
        :return: The data from the url if applicable.
        :rtype: Optional[dict]
        """

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: YTDL.extract_info(url, download=False)
            )
        except youtube_dl.utils.DownloadError:
            return None

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

        if DEEZER_RE.match(query) or SOUNDCLOUD_RE.match(query):
            data = await self.fetch_ytdl_data(query)
            if not data:
                return []

            return [
                Player(
                    requester,
                    query,
                    data["title"],
                    data["url"],
                    data["webpage_url"],
                    data.get("duration", 30),
                    data,
                    True,
                )
            ]

        return await Player.make_players(self.youtube, query, requester)

    @ensure_connection()
    async def queue_add(
        self,
        ctx: commands.Context,
        players: List[Player],
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

        if ctx.guild.id in self.queue:
            self.queue[ctx.guild.id].queue += players
        else:
            self.queue[ctx.guild.id] = QueueManager(self.default_volume, players)

        return True

    @ensure_connection(check_queue=True)
    async def queue_remove(self, ctx: commands.Context, index: int) -> Optional[Player]:
        """
        |coro|

        Removes a player from the queue in ctx at the specified index.
        Calls on_music_error with RemoveIndexInvalid if index is invalid.

        :param ctx: The context.
        :type ctx: commands.Context
        :param index: The index.
        :type index: int
        :return: The player that was removed, if applicable.
        :rtype: Optional[Player]
        """

        try:
            queue = self.queue[ctx.guild.id]

            return queue.remove(queue.pos + index)
        except IndexError:
            await self.call_event(
                "on_music_error",
                ctx,
                RemoveIndexInvalid("Failure when removing player from queue"),
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

    @ensure_connection()
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

        if not ctx.voice_client.is_playing():
            await self._check_queue(ctx)
            return True

    @ensure_connection()
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

        if ctx.voice_client.is_paused():
            await self.call_event(
                "on_music_error", ctx, AlreadyPaused("Player is already paused.")
            )
            return

        if self.type == ManagerType.LAVALINK:
            await ctx.voice_client.set_pause(pause=True)
        else:
            (await self.now_playing(ctx)).last_pause_timestamp = time.time()
            ctx.voice_client.pause()

        create_task(self.bot.loop, self.ensure_activity(ctx))
        return True

    @ensure_connection()
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

        if not ctx.voice_client.is_paused():
            await self.call_event(
                "on_music_error", ctx, NotPaused("Player is not paused")
            )
            return

        if self.type == ManagerType.LAVALINK:
            await ctx.voice_client.set_pause(pause=False)
        else:
            ctx.voice_client.resume()

            now_playing = await self.now_playing(ctx)
            now_playing.start_timestamp += (
                time.time() - now_playing.last_pause_timestamp
            )

        return True

    @ensure_connection(check_playing=True, check_queue=True)
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

        await maybe_coroutine(ctx.voice_client.stop)
        return previous_players

    @ensure_connection(check_playing=True, check_queue=True)
    async def goto(self, ctx: commands.Context, index: int = 0) -> None:
        queue = self.queue[ctx.guild.id]

        queue.pos = index
        await maybe_coroutine(ctx.voice_client.stop)

    @ensure_connection(check_playing=True, check_queue=True)
    async def skip(self, ctx: commands.Context, index: int = None) -> Optional[Player]:
        """
        |coro|

        Skips to the index in ctx.
        Calls on_music_error with InvalidSkipIndex or SkipError.

        :param index: The index to skip to.
        :type index: int
        :param ctx: The context.
        :type ctx: commands.Context
        :return: The skipped player if applicable.
        :rtype: Optional[Player]
        """

        queue = self.queue[ctx.guild.id]

        # Created duplicate to make sure InvalidSkipIndex isn't raised when the user does pass an index and the queue
        # is empty.
        skip_index = 0 if index is None else index - 1
        if not skip_index < len(queue.queue) and not queue.pos < skip_index:
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
            player = queue.queue[original_position]

        await maybe_coroutine(ctx.voice_client.stop)
        return player

    @ensure_connection(check_playing=True, check_queue=True)
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
        await channel.connect(
            cls=LavalinkPlayer
            if self.type == ManagerType.LAVALINK
            else discord.VoiceClient
        )
        return channel

    @ensure_connection()
    async def leave(self, ctx: commands.Context) -> Optional[discord.VoiceChannel]:
        """
        |coro|

        Leaves the voice channel in ctx.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: The voice channel it left.
        :rtype: Optional[discord.VoiceChannel]
        """

        if ctx.guild.id in self.queue:
            self.queue[ctx.guild.id].cleanup()
            del self.queue[ctx.guild.id]

        await maybe_coroutine(ctx.voice_client.stop)

        channel = ctx.voice_client.channel
        await ctx.voice_client.disconnect(force=True)
        return channel

    @ensure_connection(check_queue=True)
    async def now_playing(self, ctx: commands.Context) -> Optional[Player]:
        """
        |coro|

        Returns the currently playing player.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: The currently playing player.
        :rtype: Optional[Player]
        """

        now_playing = self.queue[ctx.guild.id].now_playing
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await self.call_event(
                "on_music_error",
                ctx,
                NotPlaying("Client is not playing anything currently"),
            )

        return now_playing

    @ensure_connection(check_playing=True, check_queue=True)
    async def queueloop(self, ctx: commands.Context) -> Optional[bool]:
        """
        |coro|

        Toggles the queue loop.

        :param ctx: The context
        :type ctx: commands.Context
        :return: A bool indicating if the queue loop is now enabled or disabled.
        :rtype: Optional[bool]
        """

        queue = self.queue[ctx.guild.id]

        queue.loop = (
            Loops.QUEUE_LOOP
            if self.queue[ctx.guild.id].loop != Loops.QUEUE_LOOP
            else Loops.NO_LOOP
        )

        if queue.loop == Loops.QUEUE_LOOP:
            queue.queue_loop_start = queue.pos

        return queue.loop == Loops.QUEUE_LOOP

    @ensure_connection(check_playing=True, check_queue=True)
    async def shuffle(self, ctx: commands.Context) -> Optional[bool]:
        """
        |coro|

        Toggles the shuffle feature.

        :param commands.Context ctx: The context
        :return: A bool indicating if the queue loop is now enabled or disabled.
        :rtype: Optional[bool]
        """

        queue = self.queue[ctx.guild.id]

        queue.shuffle = not queue.shuffle
        if queue.shuffle:
            queue.original_queue = queue.queue

            play_queue = queue.queue[queue.pos + 1 :]
            shuffled_queue = random.sample(play_queue, len(play_queue))
            queue.queue = (
                queue.queue[: queue.pos] + [queue.now_playing] + shuffled_queue
            )

        return queue.shuffle

    @ensure_connection(check_playing=True, check_queue=True)
    async def autoplay(self, ctx: commands.Context) -> Optional[bool]:
        """
        |coro|

        Toggles the autoplay feature.

        :param commands.Context ctx: The context
        :return: A bool indicating if autoplay is now enabled or disabled.
        :rtype: Optional[bool]
        """

        self.queue[ctx.guild.id].autoplay = not self.queue[ctx.guild.id].autoplay
        return self.queue[ctx.guild.id].autoplay

    @ensure_connection(check_playing=True, check_queue=True)
    async def loop(self, ctx: commands.Context) -> Optional[bool]:
        """
        |coro|

        Toggles the loop.

        :param ctx: The context
        :type ctx: commands.Context
        :return: A bool indicating if the loop is now enabled or disabled.
        :rtype: Optional[bool]
        """

        self.queue[ctx.guild.id].loop = (
            Loops.LOOP if self.queue[ctx.guild.id].loop != Loops.LOOP else Loops.NO_LOOP
        )
        return self.queue[ctx.guild.id].loop == Loops.LOOP

    @ensure_connection(check_queue=True)
    async def get_queue(self, ctx: commands.Context) -> Optional[QueueManager]:
        """
        |coro|

        Returns the queue of ctx.

        :param ctx: The context.
        :type ctx: commands.Context
        :return: The queue.
        :rtype: Optional[QueueManager]
        """

        return self.queue[ctx.guild.id]

    @staticmethod
    def parse_duration(duration: Union[str, float], hour_format: bool = True) -> str:
        """
        |coro|

        Returns parsed duration.

        :param bool hour_format: A bool indicating if the parse should contain hours.
        :param duration: The duration.
        :type duration: Union[str, float]
        :param duration: Format Hours.
        :type duration: bool
        :return: The parsed duration.
        :rtype: str
        """

        if duration == "LIVE":
            return duration

        time_format = "%H:%M:%S" if hour_format else "%M:%S"

        return time.strftime(time_format, time.gmtime(round(duration)))

    @ensure_connection(check_queue=True)
    async def move(
        self, ctx: commands.Context, player_index: int, new_index: int
    ) -> Optional[Player]:
        """

        :param player_index: The index of the player that you want to move.
        :param new_index: The index you want to move the player to.
        :param ctx: Context to fetch the queue from
        :return: The player object that was moved
        :rtype: Optional[Player]
        """

        queue = await self.get_queue(ctx)
        player_index += queue.pos
        new_index += queue.pos

        if new_index > len(queue.queue) or player_index > len(queue.queue):
            return await self.call_event(
                "on_music_error", ctx, InvalidSkipIndex("Skip index is invalid")
            )

        player = queue.remove(player_index)
        queue.queue.insert(new_index, player)
        return player
