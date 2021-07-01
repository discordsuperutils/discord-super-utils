import aiohttp
import discord
import youtube_dl
from .Base import *  # should be .Base, koyashie use Base for testing

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
    'default_search': 'auto',
    'source_address': '0.0.0.0'
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


class Player(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.1):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<Player title={self.title}, url={self.url}, duration={self.duration}>'

    @classmethod
    async def make_player(cls, query: str):
        try:
            data = await MusicManager.fetch_data(query)
            if data is None:
                return None
        except:
            return None

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url']
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class QueueManager:
    def __init__(self, volume, queue):
        self.queue = queue
        self.volume = volume
        self.history = []
        self.looping = False
        self.queue_loop = False

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

    def check_queue(self, ctx):
        try:
            if self.queue[ctx.guild.id].looping:
                song = self.queue[ctx.guild.id].now_playing
                player = Player(discord.FFmpegPCMAudio(song.url, **ffmpeg_options), data=song.data)

            elif self.queue[ctx.guild.id].queue_loop:
                player = self.queue[ctx.guild.id].remove(0)
                self.queue[ctx.guild.id].add(player)

                player = Player(discord.FFmpegPCMAudio(player.url, **ffmpeg_options), data=player.data)

            else:
                player = self.queue[ctx.guild.id].remove(0)

            self.queue[ctx.guild.id].now_playing = player

            if player is not None and ctx.voice_client:
                player.volume = self.queue[ctx.guild.id].volume
                ctx.voice_client.play(player, after=lambda x: self.check_queue(ctx))  # dont add spaces here after='a'

                if not self.queue[ctx.guild.id].looping and not self.queue[ctx.guild.id].queue_loop:
                    self.queue[ctx.guild.id].history.append(player)
                    self.bot.loop.create_task(
                        self.call_event('on_play', ctx, player)
                    )

        except IndexError:
            return

    @classmethod
    async def fetch_data(cls, query: str):
        """Returns a dict with info extracted from the URL/query given"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))

    @classmethod
    async def create_player(cls, query):
        return await Player.make_player(query)

    async def queue_add(self, player, ctx):
        """Adds specified player object to queue"""
        if ctx.guild.id in self.queue:
            self.queue[ctx.guild.id].add(player)
        else:
            self.queue[ctx.guild.id] = QueueManager(0.1, [player])

    async def queue_remove(self, player, ctx):
        """Removed specified player object from queue"""
        if ctx.guild.id in self.queue:
            try:
                await self.queue[ctx.guild.id].remove(player)
            except:
                await self.call_event('on_music_error', ctx, QueueError("Failure when removing player from queue"))

    async def lyrics(self, title, author, query=None):
        query = f"{title} {author}" if query is None else query
        url = f"https://some-random-api.ml/lyrics?title={query}"

        async with aiohttp.ClientSession() as session:
            request = await session.get(url)
            request_json = await request.json()

            await request_json.get('lyrics', None)

    async def play(self, ctx, player=None):
        """Plays the top of the queue or plays specified player"""
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx, NotConnected("Client is not connected to a voice channel"))
            return

        elif player is not None:
            ctx.voice_client.play(player)
            return True

        if not ctx.voice_client.is_playing():
            self.check_queue(ctx)
            return True

    async def pause(self, ctx):
        """Pauses the voice client"""
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx, NotConnected("Client is not connected to a voice channel"))
            return

        if ctx.voice_client.is_paused():
            await self.call_event('on_music_error', ctx, AlreadyPaused("Player is already paused."))

        ctx.voice_client.pause()
        return True

    async def resume(self, ctx):
        """Resumes the voice client"""
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx, NotConnected("Client is not connected to a voice channel"))
            return

        if not ctx.voice_client.is_paused():
            await self.call_event('on_music_error', ctx, NotPaused("Player is not paused"))
            return

        ctx.voice_client.resume()
        return True

    async def skip(self, ctx):
        """Most likely wont work"""
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx, NotConnected("Client is not connected to a voice channel"))
            return

        if not ctx.voice_client.is_playing():
            await self.call_event('on_music_error', ctx, NotPlaying("Client is not playing music"))
            return

        if len(self.queue[ctx.guild.id].queue) > 0:
            player = self.queue[ctx.guild.id].queue[0]
            ctx.voice_client.stop()
            return player

        await self.call_event('on_music_error', ctx, SkipError("No song to skip to."))

    async def volume(self, ctx, volume: int = None):
        """Returns the volume if volume is not given or changes the volume if it is given"""
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx, NotConnected("Client is not connected to a voice channel"))
            return

        if not ctx.voice_client.is_playing():
            await self.call_event('on_music_error', ctx, NotPlaying("Client is not playing music"))
            return

        if volume is None:
            return ctx.voice_client.source.volume * 100
        else:
            ctx.voice_client.source.volume = volume / 100
            self.queue[ctx.guild.id].volume = volume / 100
            return ctx.voice_client.source.volume * 100

    async def join(self, ctx):
        """Joins voice channel that user is in"""
        if ctx.voice_client and ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx,
                                  AlreadyConnected("Client is already connected to a voice channel"))
            return

        await ctx.author.voice.channel.connect()
        return True

    async def leave(self, ctx):
        """Leaves voice channel"""
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx, NotConnected("Client is not connected to a voice channel"))
            return

        await ctx.voice_client.disconnect()
        return True

    async def history(self, ctx):
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx, NotConnected("Client is not connected to a voice channel"))
            return

        try:
            return self.queue[ctx.guild.id].history
        except:
            await self.call_event('on_music_error', ctx, QueueEmpty("Queue is empty"))

    async def now_playing(self, ctx):
        """Returns player of currently playing song"""
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx, NotConnected("Client is not connected to a voice channel"))
            return

        if not ctx.voice_client.is_playing():
            await self.call_event('on_music_error', ctx, NotPlaying("Client is not playing anything currently"))
            return

        try:
            return self.queue[ctx.guild.id].now_playing
        except:
            await self.call_event('on_music_error', ctx, QueueEmpty("Queue is empty"))

    async def queueloop(self, ctx):
        """Sets queue loops to be on or off"""
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx, NotConnected("Client is not connected to a voice channel"))
            return

        if not ctx.voice_client.is_playing():
            await self.call_event('on_music_error', ctx, NotPlaying("Client is not playing anything currently"))
            return

        try:
            self.queue[ctx.guild.id].queue_loop = not self.queue[ctx.guild.id].queue_loop
            if self.queue[ctx.guild.id].queue_loop:
                self.queue[ctx.guild.id].add(self.queue[ctx.guild.id].now_playing)
            return self.queue[ctx.guild.id].queue_loop
        except IndexError:
            await self.call_event('on_music_error', ctx, QueueEmpty("Queue is empty"))

    async def loop(self, ctx):
        """Sets loops to be on or off"""
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx, NotConnected("Client is not connected to a voice channel"))
            return

        if not ctx.voice_client.is_playing():
            await self.call_event('on_music_error', ctx, NotPlaying("Client is not playing anything currently"))
            return

        try:
            self.queue[ctx.guild.id].looping = not self.queue[ctx.guild.id].looping
            return self.queue[ctx.guild.id].looping
        except IndexError:
            await self.call_event('on_music_error', ctx, QueueEmpty("Queue is empty"))
