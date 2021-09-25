import discordSuperUtils
from discord.ext import commands
from discordSuperUtils import MusicManager, PageManager

import datetime

#function to format duration
def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} d'.format(days))
        if hours > 0:
            duration.append('{} hr'.format(hours))
        if minutes > 0:
            duration.append('{} min'.format(minutes))
        if seconds > 0:
            duration.append('{} s'.format(seconds))

        return ', '.join(duration)

#format view, like and dislike count
def parse_count(count: int):
    if count > 1000000000:
        return f"{count//1000000000}.{(count%1000000000)//10000000} B"
    elif count > 1000000:
        return f"{count//1000000}.{(count%1000000)//100000} M"
    elif count > 1000:
        return f"{count//1000}.{(count%1000)//100} K"
    else:
        return count
      
#Music commands
class Music(commands.Cog, discordSuperUtils.CogManager.Cog, name="Music"):
    def __init__(self, bot):
        self.bot = bot
        self.skip_votes = set() #skip vote counter
        
        # self.client_secret = "" # spotify client_secret
        # self.client_id = "" # spotify client_id
        # ^^^ get your's from here https://developer.spotify.com/
        
        self.MusicManager = MusicManager(self.bot, spotify_support=False)

        # self.MusicManager = MusicManager(bot, 
        #                                  client_id=self.client_id,
        #                                  client_secret=self.client_secret, 
        #                                  spotify_support=True)

        # if using spotify support use this instead ^^^

        super().__init__()

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_music_error(self, ctx, error):
        raise error  # Add error handling here

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_play(self, ctx, player): #this returns a player object
        
        #extracting useful data from player object
        thumbnail = player.data['videoDetails']['thumbnail']['thumbnails'][-1]['url']
        title = player.data['videoDetails']['title']
        url = player.url
        uploader = player.data['videoDetails']['author']
        
        #creating an embed
        embed =(discord.Embed(
                        title= "Now Playing",
                        color = discord.Color.from_rgb(255, 255, 0),
                        timestamp = datetime.datetime.now(datetime.timezone.utc),
                        description = f"[**{title}**]({url}) by **{uploader}**"
                        )
                    .add_field(
                        name = "Requested by",
                        value = player.requester.mention
                        )
                    .set_thumbnail(
                        url = thumbnail
                            )
                    )
        #sending the embed
        await ctx.send(embed = embed)

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_queue_end(self, ctx):
        #printing on terminal
        print(f"The queue has ended in {ctx}")
        
        #sending message in channel
        await ctx.send("Queue ended")
        
        # You could wait and check activity, etc...

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_inactivity_disconnect(self, ctx):
        #printing on terminal
        print(f"I have left {ctx} due to inactivity")
        
        #sending message in channel
        await ctx.send("Left Music Channel due to inactivity")

    #optional
    @commands.Cog.listener()
    async def on_ready(self):
        print("Music manager is ready.", self.bot.user)
    #^^^ you can add this to your existing on_ready function
    
    #leave command
    @commands.command()
    async def leave(self, ctx):
        if await self.MusicManager.leave(ctx):
            await ctx.send("👋") # or await message.add_reaction("👋")
    
    #lyrics command
    @commands.command()
    async def lyrics(self, ctx, *, query = None):
        if response := await self.MusicManager.lyrics(ctx, query):
              #if lyrics are found
              title, author, lyrics = response
              
              embed = discord.Embed(
                          title = f"Lyrics for {title} by {author}",
                          color = discord.Color.from_rgb(255, 0, 255),
                          timestamp = datetime.datetime.utcnow(),
                          description = lyrics
                      )
              await ctx.send(embed = embed)
          
          else:
              await ctx.send("No lyrics were found for the song")
    
    #now playing command
    @commands.command()
    async def np(self, ctx):
        if player := await self.MusicManager.now_playing(ctx):
            #played duration
            duration_played = round(await self.MusicManager.get_player_played_duration(ctx, player))
            
            #loop status
            loop = (await self.MusicManager.get_queue(ctx)).loop
            if loop == discordSuperUtils.Loops.LOOP:
                loop_status = "Looping enabled."
            elif loop == discordSuperUtils.Loops.QUEUE_LOOP:
                loop_status = "Queue looping enabled."
            else:
                loop_status = "Looping Disabled"
            
            #fecthing other details   
            thumbnail = player.data['videoDetails']['thumbnail']['thumbnails'][-1]['url']
            title = player.data['videoDetails']['title']
            url = player.url
            uploader = player.data['videoDetails']['author']
            views = player.data['videoDetails']['viewCount']
            rating = player.data['videoDetails']['averageRating']
            
            #creating embed
            embed = 
                (discord.Embed(
                    title = 'Now playing',
                    description = f"**{title}**",
                    timestamp = datetime.datetime.utcnow(),
                    color = discord.Color.from_rgb(0, 255, 255))
                .add_field(
                    name = 'Played',
                    value = parse_duration(duration_played)
                    )
                .add_field(
                    name = 'Duration',
                    value = parse_duration(player.duration)
                    )
                .add_field(
                    name = 'Loop',
                    value = loop_status
                    )
                .add_field(
                     name = 'Requested by',
                     value = player.requester.mention
                     )
                .add_field(
                    name = 'Uploader',
                    value = uploader
                    )
                .add_field(
                    name = 'URL',
                    value = f'[Click]({url})'
                    )
                .add_field(
                    name = 'Views',
                    value = parse_count(int(views))
                    )
                .add_field(
                    name ='Rating',
                    value = rating
                    )
                .set_thumbnail(
                    url = thumbnail
                    )
                .set_image(
                    url = r"https://i.imgur.com/ufxvZ0j.gif"
                    )
                .set_author(
                    name = ctx.author.name,
                    icon_url = ctx.author.avatar_url
                    )
                )
            await ctx.send(embed=embed)
            
    @commands.command()
    async def join(self, ctx):
        if await self.MusicManager.join(ctx):
            await ctx.send("Joined Voice Channel")

    @commands.command()
    async def play(self, ctx, *, query: str):
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.MusicManager.join(ctx)

        async with ctx.typing():
            players = await self.MusicManager.create_player(query, ctx.author)

        if players:
            if await self.MusicManager.queue_add(
                players=players, ctx=ctx
            ) and not await self.MusicManager.play(ctx):
                await ctx.send("Added to queue")

        else:
            await ctx.send("Query not found.")

    @commands.command()
    async def pause(self, ctx):
        if await self.MusicManager.pause(ctx):
            await ctx.send("Player paused.")

    @commands.command()
    async def resume(self, ctx):
        if await self.MusicManager.resume(ctx):
            await ctx.send("Player resumed.")

    @commands.command()
    async def volume(self, ctx, volume: int):
        await self.MusicManager.volume(ctx, volume)

    @commands.command()
    async def loop(self, ctx):
        is_loop = await self.MusicManager.loop(ctx)
        await ctx.send(f"Looping toggled to {is_loop}")

    @commands.command()
    async def queueloop(self, ctx):
        is_loop = await self.MusicManager.queueloop(ctx)
        await ctx.send(f"Queue looping toggled to {is_loop}")

    @commands.command()
    async def history(self, ctx):
        formatted_history = [
            f"Title: '{x.title}'\nRequester: {x.requester.mention}"
            for x in (await self.MusicManager.get_queue(ctx)).history
        ]

        embeds = discordSuperUtils.generate_embeds(
            formatted_history,
            "Song History",
            "Shows all played songs",
            25,
            string_format="{}",
        )

        page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
        await page_manager.run()

    @commands.command()
    async def skip(self, ctx, index: int = None):
        await self.MusicManager.skip(ctx, index)

    @commands.command()
    async def queue(self, ctx):
        formatted_queue = [
            f"Title: '{x.title}\nRequester: {x.requester.mention}"
            for x in (await self.MusicManager.get_queue(ctx)).queue
        ]

        embeds = discordSuperUtils.generate_embeds(
            formatted_queue,
            "Queue",
            f"Now Playing: {await self.MusicManager.now_playing(ctx)}",
            25,
            string_format="{}",
        )

        page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
        await page_manager.run()

#cog adding statement
