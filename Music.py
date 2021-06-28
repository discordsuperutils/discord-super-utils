import urllib.request , discord, youtube_dl, re, requests, json

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

class QueueError(Exception):
    """Raises error when something is wrong with the queue"""

def get_data(url):
    """Returns a dict with info extracted from the URL given"""
    info = ytdl.extract_info(str(url), download=False)
    return info

def search(query):
    """Returns URL of a video from Youtube"""
    query = query.replace(" ", "+")
    info = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + query)
    video_ids = re.findall(r"watch\?v=(\S{11})", info.read().decode())
    url = ("https://www.youtube.com/watch?v=" + video_ids[0])
    return url

class Player(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.1):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

    @classmethod
    async def make_player(cls, url:str):
        data = ytdl.extract_info(url, download=False)
        if 'entries' in data:
            data = data['entries'][0]
        print(data)
        filename = data['url']
        player = cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        return player

class MusicManager:
    def __init__(self, queue=None):
        self.queue = queue

    async def fetch_data(self, url):
        """Returns a dict with info extracted from the URL given"""
        info = ytdl.extract_info(str(url), download=False)
        return info

    def check_queue(self, ctx):
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
        ctx.voice_client.play(player= player, after = lambda x: self.check_queue(ctx))

    async def search(self, query:str):
        """Returns URL of a video from Youtube"""
        arg1 = query.replace(" ", "+")
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + arg1)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        url = ("https://www.youtube.com/watch?v=" + video_ids[0])
        return url

    async def create_player(self, url):
        return await Player.make_player(url=url)
    
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
                raise QueueError("Failure to remove player from the queue")
        elif type(self.queue) is dict:
            if ctx.guild.id in self.queue:
                try:
                    self.queue[ctx.guild.id].remove(player)
                except:
                    raise QueueError("Failure to remove player from the queue")
            

    async def play(self, ctx, player=None):
        """Plays the top of the queue or plays specified player"""
        if ctx.voice_client and ctx.voice_client.is_connected():
            if ctx.voice_client.is_playing():
                raise AlreadyPlaying("Player is already playing audio")
            elif not player is None:
                ctx.voice_client.play(player)
            elif type(self.queue) is list:
                try:
                    ctx.voice_client.play(self.queue[0], after = lambda x: self.check_queue(ctx))
                    return self.queue[0]
                except IndexError:
                    raise QueueEmpty("Queue is empty.")
            elif type(self.queue ) is dict:
                if ctx.guild.id in self.queue:
                    try:
                        ctx.voice_client.play(self.queue[ctx.guild.id][0], after = lambda x: self.check_queue(ctx))
                        return self.queue[ctx.guild.id][0]
                    except IndexError:
                        raise QueueEmpty("Queue is empty.")
        else:
            raise NotConnected("Need to be connected to a voice channel.")

    async def pause(self, ctx):
        """Pauses the voice client"""
        if ctx.voice_client and ctx.voice_client.is_connected():
            try:
                ctx.voice_client.pause()
            except:
                raise NotPaused("Player is either already paused or not connected to voice.")

    async def resume(self, ctx):
        """Resumes the voice client"""
        if ctx.voice_client and ctx.voice_client.is_connected():
            try:
                ctx.voice_client.resume()
            except:
                raise AlreadyPlaying("Player is either already playing or not connected to voice.")

    async def skip(self, ctx):
        """Most likely wont work"""
        if ctx.voice_client and ctx.voice_client.is_connected():
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()

    async def volume(self, ctx, volume: int = None):
        """Returns the volume if volume is not given or changes the volume if it is given"""
        if volume is None:
            return ctx.voice_client.source.volume * 100
        else:
            ctx.voice_client.source.volume = volume / 100
            return ctx.voice_client.source.volume * 100

    async def join(self, ctx):
        """Joins voice channel that user is in"""
        if ctx.voice_client:
            if ctx.voice_client.is_connected():
                raise AlreadyConnected("Client is already connected to a voice channel")
            else:
                await ctx.author.voice.channel.connect()
        else:
            await ctx.author.voice.channel.connect()

    async def leave(self, ctx):
        """Leaves voice channel"""
        if ctx.voice_client:
            if ctx.voice_client.is_connected():
                await ctx.voice_client.disconnect()
            else:
                raise NotConnected("Client is not connected to a voice channel")
        else:
            raise NotConnected("Client is not connected to a voice channel")

    async def now_playing(self, ctx):
        """Returns player of currently playing song"""
        if ctx.voice_client and ctx.voice_client.is_connected():
            if ctx.voice_client.is_playing():
                if type(self.queue) is list:
                    try:
                        return self.queue[0]
                    except:
                        raise QueueEmpty("Queue is empty")
                elif type(self.queue) is dict:
                    try:
                        return self.queue[ctx.guild.id][0]
                    except:
                        raise QueueEmpty("Queue is empty")
            else:
                raise NotPlaying("Player is not playing anything currently")
        else:
            raise NotConnected("Client is not connected to voice currently")

    async def queue(self):
        return self.queue
