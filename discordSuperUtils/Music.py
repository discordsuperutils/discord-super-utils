import aiohttp
import discord
import youtube_dl
from .Base import EventManager
from typing import Optional
import asyncio
from enum import Enum

# should be .Base, koyashie use Base for testing

# just some options etc.

ytdl_opts = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto'
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_opts)


# errors/exceptions

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
    def __init__(self, source, *, data, volume=0.1):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration') if data.get('duration') != 0 else "LIVE"

    def __str__(self):
        return self.title

    @classmethod
    async def make_player(cls, query: str):
        data = await MusicManager.fetch_data(query)
        if data is None:
            await self.call_event('on_music_error', ctx, FetchFailed("Failed to fetch query data."))
            return []

        if 'entries' in data:
            return [cls(discord.FFmpegPCMAudio(player['url'],
                                               **ffmpeg_options), data=player) for player in data['entries']]

        filename = data['url']
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class QueueManager:
    def __init__(self, volume, queue):
        self.queue = queue
        self.volume = volume
        self.history = []
        self.loop = Loops.NO_LOOP
        self.now_playing = None

    def add(self, player):
        self.queue.append(player)

    def clear(self):
        self.queue.clear()

    def remove(self, index):
        return self.queue.pop(index)


class MusicManager(EventManager):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.queue = {}

    async def __check_connection(self, ctx, check_playing: bool = False, check_queue: bool = False) -> Optional[bool]:
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

    def __check_queue(self, ctx):
        try:
            if self.queue[ctx.guild.id].loop == Loops.LOOP:
                song = self.queue[ctx.guild.id].now_playing
                player = Player(discord.FFmpegPCMAudio(song.url, **ffmpeg_options), data=song.data)

            elif self.queue[ctx.guild.id].loop == Loops.QUEUE_LOOP:
                player = self.queue[ctx.guild.id].remove(0)
                self.queue[ctx.guild.id].add(player)

                player = Player(discord.FFmpegPCMAudio(player.url, **ffmpeg_options), data=player.data)

            else:
                player = self.queue[ctx.guild.id].remove(0)

            self.queue[ctx.guild.id].now_playing = player

            if player is not None and ctx.voice_client:
                player.volume = self.queue[ctx.guild.id].volume
                ctx.voice_client.play(player, after=lambda x: self.__check_queue(ctx))

                if self.queue[ctx.guild.id].loop == Loops.NO_LOOP:
                    self.queue[ctx.guild.id].history.append(player)
                    self.bot.loop.create_task(
                        self.call_event('on_play', ctx, player)
                    )
        except (IndexError, KeyError):
            return

    @staticmethod
    async def fetch_data(query: str):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))

    @staticmethod
    async def create_player(query):
        return await Player.make_player(query)

    async def queue_add(self, player, ctx):
        """Adds specified player object to queue"""

        if ctx.guild.id in self.queue:
            for song in player:
                self.queue[ctx.guild.id].add(song)
        else:
            self.queue[ctx.guild.id] = QueueManager(0.1, player)

    async def queue_remove(self, ctx, index):
        """Removed specified player object from queue"""

        if not await self.__check_connection(ctx, check_queue=True):
            return

        try:
            await self.queue[ctx.guild.id].remove(index)
        except IndexError:
            await self.call_event('on_music_error', ctx, QueueError("Failure when removing player from queue"))

    async def lyrics(self, ctx, query=None):
        query = self.now_playing(ctx) if query is None else query
        url = f"https://some-random-api.ml/lyrics?title={query}"

        async with aiohttp.ClientSession() as session:
            request = await session.get(url)
            request_json = await request.json()

            return await request_json.get('lyrics', None)

    async def play(self, ctx, player=None):
        if not await self.__check_connection(ctx):
            return

        if player is not None:
            ctx.voice_client.play(player)
            return True

        if not ctx.voice_client.is_playing():
            self.__check_queue(ctx)
            return True

    async def pause(self, ctx):
        if not await self.__check_connection(ctx):
            return

        if ctx.voice_client.is_paused():
            await self.call_event('on_music_error', ctx, AlreadyPaused("Player is already paused."))
            return

        ctx.voice_client.pause()
        return True

    async def resume(self, ctx):
        if not await self.__check_connection(ctx):
            return

        if not ctx.voice_client.is_paused():
            await self.call_event('on_music_error', ctx, NotPaused("Player is not paused"))
            return

        ctx.voice_client.resume()
        return True

    async def skip(self, ctx, index=None):
        if not await self.__check_connection(ctx, True, check_queue=True):
            return

        # Created duplicate to make sure InvalidSkipIndex isn't raised when the user does pass an index and the queue
        # is empty.
        skip_index = 0 if index is None else index - 1
        if not -1 < skip_index < len(self.queue[ctx.guild.id].queue):
            if index:
                await self.call_event('on_music_error', ctx, InvalidSkipIndex("Skip index invalid."))
                return

        if len(self.queue[ctx.guild.id].queue) > skip_index:
            if skip_index > 0:
                removed_songs = self.queue[ctx.guild.id].queue[:skip_index]

                self.queue[ctx.guild.id].queue = self.queue[ctx.guild.id].queue[skip_index:]
                if self.queue[ctx.guild.id].queue_loop:
                    self.queue[ctx.guild.id].queue += removed_songs

            player = self.queue[ctx.guild.id].queue[0]
            ctx.voice_client.stop()
            return player

        await self.call_event('on_music_error', ctx, SkipError("No song to skip to."))

    async def volume(self, ctx, volume: int = None):
        if not await self.__check_connection(ctx, True, check_queue=True):
            return

        if volume is None:
            return ctx.voice_client.source.volume * 100

        ctx.voice_client.source.volume = volume / 100
        self.queue[ctx.guild.id].volume = volume / 100
        return ctx.voice_client.source.volume * 100

    async def join(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx,
                                  AlreadyConnected("Client is already connected to a voice channel"))
            return

        if not ctx.author.voice:
            await self.call_event('on_music_error', ctx, UserNotConnected("User is not connected to a voice channel"))
            return

        await ctx.author.voice.channel.connect()
        return True

    async def leave(self, ctx):
        if not await self.__check_connection(ctx):
            return

        await ctx.voice_client.disconnect()
        return True

    async def history(self, ctx):
        if not await self.__check_connection(ctx, check_queue=True):
            return

        return self.queue[ctx.guild.id].history

    async def now_playing(self, ctx):
        if not await self.__check_connection(ctx, check_playing=True, check_queue=True):
            return

        return self.queue[ctx.guild.id].now_playing

    async def queueloop(self, ctx):
        if not await self.__check_connection(ctx, check_playing=True, check_queue=True):
            return

        self.queue[ctx.guild.id].loop = Loops.QUEUE_LOOP if self.queue[ctx.guild.id].loop != Loops.QUEUE_LOOP else\
            Loops.NO_LOOP

        if self.queue[ctx.guild.id].loop == Loops.QUEUE_LOOP:
            self.queue[ctx.guild.id].add(self.queue[ctx.guild.id].now_playing)

        return self.queue[ctx.guild.id].loop == Loops.QUEUE_LOOP

    async def loop(self, ctx):
        if not await self.__check_connection(ctx, check_playing=True, check_queue=True):
            return

        self.queue[ctx.guild.id].loop = Loops.LOOP if self.queue[ctx.guild.id].loop != Loops.LOOP else Loops.NO_LOOP
        return self.queue[ctx.guild.id].loop == Loops.LOOP

    def get_queue(self, ctx):
        return self.queue[ctx.guild.id].queue
