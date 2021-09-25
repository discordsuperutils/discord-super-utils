import discord
from discord.ext import commands

import discordSuperUtils
from discordSuperUtils import MusicManager, PageManager

import datetime
import time
from typing import Optional

#function to format duration
def parse_duration(duration: Optional[float]) -> str:
    return (
        time.strftime("%H:%M:%S", time.gmtime(duration))
        if duration != "LIVE"
        else duration
    )

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
        errors = {
            discordSuperUtils.NotPlaying: "I am not playing anything!",
            discordSuperUtils.NotConnected: "I am not connected to a voice channel!",
            discordSuperUtils.NotPaused: "The currently playing player is not paused!",
            discordSuperUtils.QueueEmpty: "The queue is empty!",
            discordSuperUtils.AlreadyConnected: "I am already connected to a voice channel!",
            discordSuperUtils.QueueError: "There has been a queue error!",
            discordSuperUtils.SkipError: "There is no song to skip to!",
            discordSuperUtils.UserNotConnected: "User is not connected to a voice channel!",
            discordSuperUtils.InvalidSkipIndex: "That skip index is invalid!",
        }

        embed = discord.Embed(title="Error!", color=0xFF0000)

        for error_type, response in errors.items():
            if isinstance(error, error_type):
                embed.description = response
                await ctx.send(embed=embed)
                return

        print("unexpected error")
        raise error

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_play(self, ctx, player): #this returns a player object
        
        #extracting useful data from player object
        thumbnail = player.data['videoDetails']['thumbnail']['thumbnails'][-1]['url']
        title = player.data['videoDetails']['title']
        url = player.url
        uploader = player.data['videoDetails']['author']
        
        #creating an embed
        embed = discord.Embed(
            title= "Now Playing",
            color = discord.Color.from_rgb(255, 255, 0),
            timestamp = datetime.datetime.now(datetime.timezone.utc),
            description = f"[**{title}**]({url}) by **{uploader}**"
            )
        embed.add_field(
            name = "Requested by",
            value = player.requester.mention
            )
        embed.set_thumbnail(
            url = thumbnail
            )
                
        #sending the embed
        await ctx.send(embed = embed)
        #clearing skip votes for each song
        self.skip_votes.clear()

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
            title, author, query_lyrics = response
            

            splitted = query_lyrics.split("\n")
            res = []
            current = ""
            for i, split in enumerate(splitted):
                if len(splitted) <= i + 1 or len(current) + len(splitted[i + 1]) > 1024:
                    res.append(current)
                    current = ""
                    continue
                current += split + "\n"
            #creating embeds list for page manager
            embeds = [
                        discord.Embed(
                            title=f"Lyrics for '{title}' by '{author}', (Page {i + 1}/{len(res)})",
                            description=x,
                            )
                        for i, x in enumerate(res)
                    ]
            #editing the embeds
            for embed in embeds:
                embed.timestamp = datetime.datetime.utcnow()

            page_manager = discordSuperUtils.PageManager(
                ctx,
                embeds,
                public=True,
            )
            
            await page_manager.run()
          
        else:
            await ctx.send("No lyrics were found for the song")
    
    #now playing command
    @commands.command()
    async def now_playing(self, ctx):
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
            embed = discord.Embed(
                title = 'Now playing',
                description = f"**{title}**",
                timestamp = datetime.datetime.utcnow(),
                color = discord.Color.from_rgb(0, 255, 255)
                )
            embed.add_field(
                name = 'Played',
                value = parse_duration(duration_played)
                )
            embed.add_field(
                name = 'Duration',
                value = parse_duration(player.duration)
                )
            embed.add_field(
                name = 'Loop',
                value = loop_status
                )
            embed.add_field(
                name = 'Requested by',
                value = player.requester.mention
                )
            embed.add_field(
                name = 'Uploader',
                value = uploader
                )
            embed.add_field(
                name = 'URL',
                value = f'[Click]({url})'
                )
            embed.add_field(
                name = 'Views',
                value = parse_count(int(views))
                )
            embed.add_field(
                name ='Rating',
                value = rating
                )
            embed.set_thumbnail(
                url = thumbnail
                )
            embed.set_image(
                url = r"https://i.imgur.com/ufxvZ0j.gif"
                )
            embed.set_author(
                name = ctx.author.name,
                icon_url = ctx.author.avatar_url
                )

            #sending the embed
            await ctx.send(embed=embed)

    #join command        
    @commands.command()
    async def join(self, ctx):
        if await self.MusicManager.join(ctx):
            await ctx.send("Joined Voice Channel")

    #play command
    @commands.command()
    async def play(self, ctx, *, query: str):
        #checking if the bot has joined a voice channel
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            await self.MusicManager.join(ctx)

        #searching while showing typing status
        async with ctx.typing(): 
            players = await self.MusicManager.create_player(query, ctx.author)
        #^change to async ctx.defer() if using slash commands

        #if a player object is created ie. song found
        if players:
            if await self.MusicManager.queue_add(
                players=players, 
                ctx=ctx
            ) and not await self.MusicManager.play(ctx):
                #sending a message
                await ctx.send(f"Added {players[0].title} to song queue.")

        else:
            await ctx.send("Query not found.")

    #pause command
    @commands.command()
    async def pause(self, ctx):
        if await self.MusicManager.pause(ctx):
            await ctx.send("Paused")

    #resume command
    @commands.command()
    async def resume(self, ctx):
        if await self.MusicManager.resume(ctx):
            await ctx.send("Resumed")

    #volume command
    @commands.command()
    async def volume(self, ctx, volume: int):
        await self.MusicManager.volume(ctx, volume)
        await ctx.send(f"Volume set to {volume}%")

    #song loop command
    @commands.command()
    async def loop(self, ctx):
        is_loop = await self.MusicManager.loop(ctx)
        
        if is_loop == True:
            await ctx.send(f"Looping Enabled")
        else:
            await ctx.send(f"Looping Disabled")

    #queue loop command
    @commands.command()
    async def queueloop(self, ctx):
        is_loop = await self.MusicManager.queueloop(ctx)
        
        if is_loop:
            await ctx.send(f"Queue looping enabled")
        else:
            await ctx.send(f"Queue looping disabled")

    #history
    @commands.command()
    async def history(self, ctx):
        history = (await self.MusicManager.get_queue(ctx)).queue
        #checking if history is empty or not
        if history == []:
            formatted_history = ["Empty history"]
        else:
            formatted_history = [
                f"Title: '{x.title}\nRequester: {x.requester.mention}"
                for x in history
            ]

        embeds = discordSuperUtils.generate_embeds(
            formatted_history,
            "Song History",
            "Shows all played songs",
            25,
            string_format="{}",
        )
        
        for embed in embeds:
            embed.timestamp = datetime.datetime.utcnow()

        await discordSuperUtils.PageManager(
                ctx, 
                embeds, 
                public=True
            ).run()
    #stop command
    @commands.command()
    async def stop(self, ctx):
        await self.MusicManager.cleanup(ctx.voice_client, ctx.guild)
        await ctx.send("⏹️")

    #skip command with voting
    @commands.command()
    async def skip(self, ctx, index: int = None):
        if player := await self.MusicManager.now_playing(ctx):
            #getting the queue
            queue = (await self.MusicManager.get_queue(ctx)).queue
            
            #checking if queue is empty or not
            if queue == []:
                await ctx.send("Can't skip the last song of queue.")
  
            else:
                #checking the voter
                voter = ctx.author
                #if voter is requester than skips automatically
                if voter == player.requester:
                    await ctx.send('Skipped by requester')
                    await self.MusicManager.skip(ctx, index)
                #voting
                elif voter.id not in self.skip_votes: #checking if someone already votes
                    self.skip_votes.add(voter.id)
                    total_votes = len(self.skip_votes)
                    #if total votes >=3 then it will skip
                    if total_votes >= 3:
                        await ctx.send('Skipped on vote')
                        await self.MusicManager.skip(ctx, index)
                        #clearing skip votes
                        self.skip_votes.clear()
                    #shows voting status
                    else:
                        await ctx.send(f'Skip vote added, currently at **{total_votes}/3**')
                #if someone uses vote command twice
                else:
                    await ctx.send('You have already voted to skip this song.')
                
        else:
            await ctx.send('Not playing any music right now...')
    
    #queue command
    @commands.command()
    async def queue(self, ctx):
        queue = (await self.MusicManager.get_queue(ctx)).queue
        #checking if queue is empty or not
        if queue == []:
            formatted_queue = ["Empty queue"]
        else:
            formatted_queue = [
                f"Title: '{x.title}\nRequester: {x.requester.mention}"
                for x in queue
            ]

        embeds = discordSuperUtils.generate_embeds(
            formatted_queue,
            "Queue",#title of embed
            f"Now Playing: {await self.MusicManager.now_playing(ctx)}",
            25, #number of rows in one pane
            string_format="{}",
            color = 11658814 #color of embed in decimal color
        )

        for embed in embeds:
            embed.timestamp = datetime.datetime.utcnow()

        await discordSuperUtils.PageManager(ctx, embeds, public=True).run()
    
    #loop status
    @commands.command()
    async def loop_check(self, ctx):
        if queue := await self.MusicManager.get_queue(ctx):
            loop = queue.loop
            loop_status = None

            if loop == discordSuperUtils.Loops.LOOP:
                loop_status = "Looping enabled."

            elif loop == discordSuperUtils.Loops.QUEUE_LOOP:
                loop_status = "Queue looping enabled."

            elif loop == discordSuperUtils.Loops.NO_LOOP:
                loop_status = "No loop enabled."

            if loop_status:
                embed = discord.Embed(
                    title = loop_status, 
                    color = 0x00FF00,
                    timestamp = datetime.datetime.utcnow()
                )

                await ctx.send(embed = embed)
    
    #before invoke checks. add more commands if you wish to
    @join.before_invoke
    @play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Bot is already in a voice channel.')

#add cog to the bot
