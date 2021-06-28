import urllib, discord, youtube_dl, re

#just some options etc. 

ytdl_opts= {
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


#errors/exceptions

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

def get_data(url):
    """Returns a dict with info extracted from the URL given"""
    info = ytdl.extract_info(str(url), download=False)
    return info

async def search(query):
    """Returns URL of a video from Youtube"""
    query = query.replace(" ", "+")
    info = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + query)
    video_ids = re.findall(r"watch\?v=(\S{11})", info.read().decode())
    url = ("https://www.youtube.com/watch?v=" + video_ids[0])
    return url

async def fetch_data(url):
    """Returns a dict with info extracted from the URL given"""
    info = ytdl.extract_info(str(url), download=False)
    return info

async def check_queue(ctx, queue):
    """Checks the queue, if song is in queue, it auto plays; if song is not in queue it leaves the voice channel."""
    """Must pass context and queue as parameter else it would break"""
    """It's reccomended users make their own queueing system as this one is prone to breaking"""
    """DONT USE THIS IT IS STILL IN TESTING"""
    if type(queue) is list:
        try:
            player = queue[0]
        except IndexError:
            return
    elif type(queue) is dict:
        try:
            player = queue[ctx.guild.id][0]
        except IndexError:
            return

    await ctx.send(f"Now playing: {player.title}")
    ctx.voice_client.play(player, after = None)
    
class music(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.1):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

    @classmethod
    async def create_player(cls, **kwargs):
        url = kwargs.get("url")
        data = get_data(url)
        filename = data['url']
        player = cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        return player   

class Player:
    def __init__(self):
        """The class that has to do with playing music"""
    
    async def play(ctx, player, after = None):
        if ctx.voice_client:
            if ctx.voice_client.is_connected():
                if ctx.voice_client.is_playing():
                    raise AlreadyPlaying("Player is already playing audio")
                else:
                    ctx.voice_client.play(player, after = after)
            else:
                raise NotConnected("Need to be connected to a voice channel.")

    async def pause(ctx):
        """Pauses the voice client"""
        try:
            ctx.voice_client.pause()
        except:
            raise NotPaused("Player is either already paused or not connected to voice.")

    async def resume(ctx):
        """Resumes the voice client"""
        try:
            ctx.voice_client.resume()
        except:
            raise AlreadyPlaying("Player is either already playing or not connceted to voice.")

    async def skip(ctx):
        """Most likely wont work"""
        ctx.voice_client.stop()

    async def volume(ctx, volume: int = None):
        """Returns the volume if volume is not given or changes the volume if it is given"""
        if volume is None:
            return (ctx.voice_client.source.volume * 100)
        else:
            ctx.voice_client.source.volume = volume / 100
            return (ctx.voice_client.source.volume * 100)

    async def join(ctx):
        """Joins voice channel that user is in"""
        if ctx.voice_client:
            if ctx.voice_client.is_connected():
                raise AlreadyConnected("Client is already connected to a voice channel")
            else:
                await ctx.author.voice.channel.connect()
        else:
            await ctx.author.voice.channel.connect()

    async def leave(ctx):
        """Leaves voice channel"""
        if ctx.voice_client:
            if ctx.voice_client.is_connected():
                await ctx.voice_client.disconnect()
            else:
                raise NotConnected("Client is not connected to a voice channel")
        else:
            raise NotConnected("Client is not connected to a voice channel")