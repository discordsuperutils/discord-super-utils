import discord
from discord.ext import commands

import discordSuperUtils
from discordSuperUtils import MusicManager, PageManager

import datetime
import time
from typing import Optional

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("-"),
    intents=discord.Intents.all(),
)


# Format duration
def parse_duration(duration: Optional[float]) -> str:
    return (
        time.strftime("%H:%M:%S", time.gmtime(duration))
        if duration != "LIVE"
        else duration
    )


# Format view count
def parse_count(count):
    original_count = count

    count = float("{:.3g}".format(count))
    magnitude = 0
    matches = ["", "K", "M", "B", "T", "Qua", "Qui"]

    while abs(count) >= 1000:
        if magnitude >= 5:
            break

        magnitude += 1
        count /= 1000.0

    try:
        return "{}{}".format(
            "{:f}".format(count).rstrip("0").rstrip("."), matches[magnitude]
        )
    except IndexError:
        return original_count


# Music commands
class Music(commands.Cog, discordSuperUtils.CogManager.Cog, name="Music"):
    def __init__(self, bot):
        self.bot = bot
        self.skip_votes = {}  # Skip vote counter dictionary

        # self.client_secret = "" # spotify client_secret
        # self.client_id = "" # spotify client_id

        # Get your's from here https://developer.spotify.com/

        self.MusicManager = MusicManager(self.bot, spotify_support=False)

        # self.MusicManager = MusicManager(bot,
        #                                  client_id=self.client_id,
        #                                  client_secret=self.client_secret,
        #                                  spotify_support=True)

        # If using spotify support use this instead ^^^

        self.ImageManager = discordSuperUtils.ImageManager()
        super().__init__()
        self.client.ImageManager = self.ImageManager
    
    # Play function
    async def play_cmd(self, ctx, query):
        async with ctx.typing():
            player = await self.MusicManager.create_player(query, ctx.author)
        
        if player:
            if not ctx.voice_client or not ctx.voice_client.is_connected():
                await self.MusicManager.join(ctx)

            await self.MusicManager.queue_add(players=player, ctx=ctx)

            if not await self.MusicManager.play(ctx):
                await ctx.send(f"Added {player[0].title} to song queue.")
            else:
                await ctx.send("✅")
        else:
            await ctx.send("Query not found.")

    # cog error handler
    async def cog_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        print("An error occurred: {}".format(str(error)))

    # Error handler
    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_music_error(self, ctx, error):
        errors = {
            discordSuperUtils.NotPlaying: "Not playing any music right now...",
            discordSuperUtils.NotConnected: f"Bot not connected to a voice channel!",
            discordSuperUtils.NotPaused: "Player is not paused!",
            discordSuperUtils.QueueEmpty: "The queue is empty!",
            discordSuperUtils.AlreadyConnected: "Already connected to voice channel!",
            discordSuperUtils.QueueError: "There has been a queue error!",
            discordSuperUtils.SkipError: "There is no song to skip to!",
            discordSuperUtils.UserNotConnected: "User is not connected to a voice channel!",
            discordSuperUtils.InvalidSkipIndex: "That skip index is invalid!",
        }

        for error_type, response in errors.items():
            if isinstance(error, error_type):
                await ctx.send(response)
                return

        print("unexpected error")
        raise error

    # On music play event
    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_play(self, ctx, player):  # This returns a player object

        # Extracting useful data from player object
        thumbnail = player.data["videoDetails"]["thumbnail"]["thumbnails"][-1]["url"]
        title = player.data["videoDetails"]["title"]
        url = player.url
        uploader = player.data["videoDetails"]["author"]
        requester = player.requester.mention if player.requester else "Autoplay"

        embed = discord.Embed(
            title="Now Playing",
            color=discord.Color.from_rgb(255, 255, 0),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            description=f"[**{title}**]({url}) by **{uploader}**",
        )
        embed.add_field(name="Requested by", value=requester)
        embed.set_thumbnail(url=thumbnail)

        await ctx.send(embed=embed)
        # Clearing skip votes for each song
        if self.skip_votes.get(ctx.guild.id):
            self.skip_votes.pop(ctx.guild.id)

    # On queue end event
    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_queue_end(self, ctx):
        print(f"The queue has ended in {ctx}")
        await ctx.send("Queue ended")
        # You could wait and check activity, etc...

    # On inactivity disconnect event
    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_inactivity_disconnect(self, ctx):
        print(f"I have left {ctx} due to inactivity")
        await ctx.send("Left Music Channel due to inactivity")

    # On ready event
    @commands.Cog.listener()
    async def on_ready(self):
        print("Music manager is ready.", self.bot.user)

    # You can add this to your existing on_ready function

    # Leave command
    @commands.command()
    async def leave(self, ctx):
        if await self.MusicManager.leave(ctx):
            await ctx.send("👋")
            # Or
            # await message.add_reaction("👋")

    # Lyrics command
    @commands.command()
    async def lyrics(self, ctx, *, query=None):
        if response := await self.MusicManager.lyrics(ctx, query):
            # If lyrics are found
            title, author, query_lyrics = response
            # Formatting the lyrics
            splitted = query_lyrics.split("\n")
            res = []
            current = ""
            for i, split in enumerate(splitted):
                if len(splitted) <= i + 1 or len(current) + len(splitted[i + 1]) > 1024:
                    res.append(current)
                    current = ""
                    continue
                current += split + "\n"
            # Creating embeds list for PageManager
            embeds = [
                discord.Embed(
                    title=f"Lyrics for '{title}' by '{author}', (Page {i + 1}/{len(res)})",
                    description=x,
                )
                for i, x in enumerate(res)
            ]
            # editing the embeds
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

    # Now playing command
    @commands.command()
    async def now_playing(self, ctx):
        if player := await self.MusicManager.now_playing(ctx):
            # Played duration
            duration_played = round(
                await self.MusicManager.get_player_played_duration(ctx, player)
            )

            # Loop status
            loop = (await self.MusicManager.get_queue(ctx)).loop
            if loop == discordSuperUtils.Loops.LOOP:
                loop_status = "Looping enabled."
            elif loop == discordSuperUtils.Loops.QUEUE_LOOP:
                loop_status = "Queue looping enabled."
            else:
                loop_status = "Looping Disabled"

            # Fecthing other details
            thumbnail = player.data["videoDetails"]["thumbnail"]["thumbnails"][-1][
                "url"
            ]
            title = player.data["videoDetails"]["title"]
            url = player.url
            uploader = player.data["videoDetails"]["author"]
            views = player.data["videoDetails"]["viewCount"]
            rating = player.data["videoDetails"]["averageRating"]
            requester = player.requester.mention if player.requester else "Autoplay"

            embed = discord.Embed(
                title="Now playing",
                description=f"**{title}**",
                timestamp=datetime.datetime.utcnow(),
                color=discord.Color.from_rgb(0, 255, 255),
            )
            embed.add_field(name="Played", value=parse_duration(duration_played))
            embed.add_field(name="Duration", value=parse_duration(player.duration))
            embed.add_field(name="Loop", value=loop_status)
            embed.add_field(name="Requested by", value=requester)
            embed.add_field(name="Uploader", value=uploader)
            embed.add_field(name="URL", value=f"[Click]({url})")
            embed.add_field(name="Views", value=parse_count(int(views)))
            embed.add_field(name="Rating", value=rating)
            embed.set_thumbnail(url=thumbnail)
            embed.set_image(url=r"https://i.imgur.com/ufxvZ0j.gif")
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

            await ctx.send(embed=embed)

    # Join voice channel command
    @commands.command()
    async def join(self, ctx):
        if await self.MusicManager.join(ctx):
            await ctx.send("Joined Voice Channel")

    # Play song command
    @commands.command()
    async def play(self, ctx, *, query: str):
        # Calling the play function
        await Music.play_cmd(self, ctx, query)

    # Pause command
    @commands.command()
    async def pause(self, ctx):
        if await self.MusicManager.pause(ctx):
            await ctx.send("Paused")

    # Resume command
    @commands.command()
    async def resume(self, ctx):
        if await self.MusicManager.resume(ctx):
            await ctx.send("Resumed")

    # Volume command
    @commands.command()
    async def volume(self, ctx, volume: int):
        if current_volume := await self.MusicManager.volume(ctx, volume) is not None:
            await ctx.send(f"Volume set to {current_volume}%")

    # Song loop command
    @commands.command()
    async def loop(self, ctx):
        is_loop = await self.MusicManager.loop(ctx)

        if is_loop is not None:
            await ctx.send(f"Looping {'Enabled' if is_loop else 'Disabled'}")

    # Queue loop command
    @commands.command()
    async def queueloop(self, ctx):
        is_loop = await self.MusicManager.queueloop(ctx)

        if is_loop is not None:
            await ctx.send(f"Queue Looping {'Enabled' if is_loop else 'Disabled'}")

    # History command
    @commands.command()
    async def history(self, ctx):
        if queue := await self.MusicManager.get_queue(ctx):
            auto = "Autoplay"
            formatted_history = [
                f"Title: '{x.title}\nRequester: {x.requester.mention if x.requester else auto}"
                for x in queue.history
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

            await discordSuperUtils.PageManager(ctx, embeds, public=True).run()

    # Stop command
    @commands.command()
    async def stop(self, ctx):
        await self.MusicManager.cleanup(ctx.voice_client, ctx.guild)
        await ctx.send("⏹️")

    # Skip command with voting
    @commands.command()
    async def skip(self, ctx, index: int = None):
        if queue := (await self.MusicManager.get_queue(ctx)):
            voter = ctx.author
            requester = (await self.MusicManager.now_playing(ctx)).requester

            # Checking if the song is autoplayed
            if requester == None:
                await ctx.send("Skipped autoplayed song")
                await self.MusicManager.skip(ctx, index)

            # Checking if queue is empty and autoplay is disabled
            elif not queue.queue and not queue.autoplay:
                await ctx.send("Can't skip the last song of queue.")

            else:
                # Checking if guild id list is in skip votes dictionary
                if not self.skip_votes.get(ctx.guild.id):
                    self.skip_votes[ctx.guild.id] = []

                # Checking the voter
                voter = ctx.author

                # If voter is requester than skips automatically
                if voter == (await self.MusicManager.now_playing(ctx)).requester:
                    skipped_player = await self.MusicManager.skip(ctx, index)
                    
                    await ctx.send("Skipped by requester")

                    if not skipped_player.requester:
                        await ctx.send("Autoplaying next song.")

                    # clearing the skip votes
                    self.skip_votes.pop(ctx.guild.id)

                # Voting
                elif (
                    voter.id not in self.skip_votes[ctx.guild.id]
                ):  # Checking if someone already voted
                    # Adding the voter id to skip votes
                    self.skip_votes[ctx.guild.id].append(voter.id)

                    # Calculating total votes
                    total_votes = len(self.skip_votes[ctx.guild.id])

                    # If total votes >=3 then it will skip
                    if total_votes >= 3:
                        skipped_player = await self.MusicManager.skip(ctx, index)
                        
                        await ctx.send("Skipped on vote")

                        if not skipped_player.requester:
                            await ctx.send("Autoplaying next song.")

                        # Clearing skip votes of the guild
                        self.skip_votes.pop(ctx.guild.id)

                    # Shows voting status
                    else:
                        await ctx.send(
                            f"Skip vote added, currently at **{total_votes}/3**"
                        )

                # If someone uses vote command twice
                else:
                    await ctx.send("You have already voted to skip this song.")

    # Queue command
    @commands.command()
    async def queue(self, ctx):
        if queue := await self.MusicManager.get_queue(ctx):
            auto = "Autoplay"
            formatted_queue = [
                f"Title: '{x.title}\nRequester: {x.requester.mention if x.requester else auto}"
                for x in queue.queue
            ]

            embeds = discordSuperUtils.generate_embeds(
                formatted_queue,
                "Queue",  # Title of embed
                f"Now Playing: {await self.MusicManager.now_playing(ctx)}",
                25,  # Number of rows in one pane
                string_format="{}",
                color=11658814,  # Color of embed in decimal color
            )

            for embed in embeds:
                embed.timestamp = datetime.datetime.utcnow()

            await discordSuperUtils.PageManager(ctx, embeds, public=True).run()

    # Loop status command
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
                    title=loop_status,
                    color=0x00FF00,
                    timestamp=datetime.datetime.utcnow(),
                )

                await ctx.send(embed=embed)

    # Autoplay command
    @commands.command()
    async def autoplay(self, ctx):
        is_autoplay = await self.MusicManager.autoplay(ctx)

        if is_autoplay is not None:
            await ctx.send(f"Autoplay toggled to {is_autoplay}")

    # Shuffle command
    @commands.command()
    async def shuffle(self, ctx):
        is_shuffle = await self.MusicManager.shuffle(ctx)

        if is_shuffle is not None:
            await ctx.send(f"Shuffle toggled to {is_shuffle}")

    # Previous/Rewind command
    @commands.command()
    async def previous(self, ctx, index: int = None):
        if previous_player := await self.MusicManager.previous(ctx, index):
            await ctx.send(f"Rewinding from {previous_player[0].title}")

    # Spotify song details of a user
    @commands.command()
    async def spotify_user_song(self, ctx, member: discord.Member = None):
        member = member if member else ctx.author
        spotify_result = next((activity for activity in member.activities if isinstance(activity, discord.Spotify)), None)

        if spotify_result is None:
            await ctx.send(f'{member.mention} is not listening to Spotify.')
            return

        image = await self.ImageManager.create_spotify_card(
            spotify_result= spotify_result,
            font_path=None
        )

        await ctx.send(file=image)

    # Spotify song from user
    @commands.command()
    async def play_user_spotify(self, ctx, member: discord.Member = None):
        member = member if member else ctx.author
        spotify_result = next((activity for activity in member.activities if isinstance(activity, discord.Spotify)), None)

        if spotify_result:
            await ctx.send(f'{member.mention} is not listening to Spotify.')
            return
        
        query = f"{spotify_result.title} {spotify_result.artist}"

        # Calling the play function
        await Music.play_cmd(self, ctx, query)

    # Before invoke checks. Add more commands if you wish to
    @join.before_invoke
    @play.before_invoke
    @play_user_spotify.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("You are not connected to any voice channel.")
            raise commands.CommandError()

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.send("Bot is already in a voice channel.")
                raise commands.CommandError()
        # Or raise a custom error


bot.add_cog(Music(bot))
bot.run("token")
