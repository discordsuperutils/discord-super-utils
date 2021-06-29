import urllib.request, discord, youtube_dl, re
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
    """Raises error when player is not playing"""


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
        data = await MusicManager.fetch_data(query)
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url']
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class MusicManager(EventManager):
    def __init__(self, queue=None):
        super().__init__()
        self.queue = queue if queue is not None else {}

    def check_queue(self, ctx):
        player = None
        if type(self.queue) is list:
            try:
                self.queue.pop(0)
                player = self.queue[0]
            except IndexError:
                return

        elif type(self.queue) is dict:
            try:
                self.queue[ctx.guild.id].pop(0)
                player = self.queue[ctx.guild.id][0]
            except IndexError:
                return

        if player is not None:
            ctx.voice_client.play(player, after=lambda x: self.check_queue(ctx))  # dont add spaces here after='a'

    @classmethod  # Useless, koyashie remove if not needed
    async def search(cls, query: str):
        """Returns URL of a video from Youtube"""
        arg1 = query.replace(" ", "+")
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + arg1)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        url = ("https://www.youtube.com/watch?v=" + video_ids[0])
        return url

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
        if type(self.queue) is list:
            self.queue.append(player)
        elif type(self.queue) is dict:
            if ctx.guild.id in self.queue:
                self.queue[ctx.guild.id].append(player)
            else:
                self.queue[ctx.guild.id] = [player]

    async def queue_remove(self, player, ctx):
        """Removed specified player object from queue"""
        if type(self.queue) is list:
            try:
                self.queue.remove(player)
            except:
                await self.call_event('on_music_error', ctx, QueueError("Failure to remove player from the queue"))
        elif type(self.queue) is dict:
            if ctx.guild.id in self.queue:
                try:
                    self.queue[ctx.guild.id].remove(player)
                except:
                    await self.call_event('on_music_error', ctx, QueueError("Failure to remove player from the queue"))

    async def play(self, ctx, player=None):
        """Plays the top of the queue or plays specified player"""
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx, NotConnected("Client is not connected to a voice channel"))
            return

        if ctx.voice_client.is_playing():
            await self.call_event('on_music_error', ctx, AlreadyPlaying("Player is already playing audio"))

        elif player is not None:
            ctx.voice_client.play(player)
            return True

        elif type(self.queue) is list:
            try:
                ctx.voice_client.play(self.queue[0], after=lambda x: self.check_queue(ctx))
                return self.queue[0]
            except IndexError:
                await self.call_event('on_music_error', ctx, QueueEmpty("Queue is empty."))

        elif type(self.queue) is dict:
            if ctx.guild.id in self.queue:
                try:
                    ctx.voice_client.play(self.queue[ctx.guild.id][0], after=lambda x: self.check_queue(ctx))
                    return self.queue[ctx.guild.id][0]
                except IndexError:
                    await self.call_event('on_music_error', ctx, QueueEmpty("Queue is empty."))

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

        ctx.voice_client.stop()
        return True

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

    async def now_playing(self, ctx):
        """Returns player of currently playing song"""
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.call_event('on_music_error', ctx, NotConnected("Client is not connected to a voice channel"))
            return

        if not ctx.voice_client.is_playing():
            await self.call_event('on_music_error', ctx, NotPlaying("Player is not playing anything currently"))
            return

        if type(self.queue) is list:
            try:
                return self.queue[0]
            except:
                await self.call_event('on_music_error', ctx, QueueEmpty("Queue is empty"))

        elif type(self.queue) is dict:
            try:
                return self.queue[ctx.guild.id][0]
            except:
                await self.call_event('on_music_error', ctx, QueueEmpty("Queue is empty"))
