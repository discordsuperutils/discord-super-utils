import discordSuperUtils
from discord.ext import commands
from discordSuperUtils import MusicManager, PageManager


bot = commands.Bot(command_prefix='-')


class Music(commands.Cog, discordSuperUtils.CogManager.Cog, name="Music"):
    def __init__(self, bot):
        self.bot = bot
        # self.client_secret = ""
        # self.client_id = ""
        self.MusicManager = MusicManager(self.bot, spotify_support=False)
        super().__init__()

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_music_error(self, ctx, error):
        raise error  # Add error handling here

    @discordSuperUtils.CogManager.event(discordSuperUtils.MusicManager)
    async def on_play(self, ctx, player):
        await ctx.send(f"Now playing: {player}")

    @commands.Cog.listener()
    async def on_ready(self):
        print('Music manager is ready.', self.bot.user)

    @commands.command()
    async def leave(self, ctx):
        if await self.MusicManager.leave(ctx):
            await ctx.send("Left Voice Channel")

    @commands.command()
    async def np(self, ctx):
        if player := await self.MusicManager.now_playing(ctx):
            await ctx.send(f"Now Playing: {player}")

    @commands.command()
    async def join(self, ctx):
        if await self.MusicManager.join(ctx):
            await ctx.send("Joined Voice Channel")

    @commands.command()
    async def play(self, ctx, *, query: str):
        async with ctx.typing():
            player = await self.MusicManager.create_player(query)

        if player:
            await self.MusicManager.queue_add(player=player, ctx=ctx)

            if not await self.MusicManager.play(ctx):
                await ctx.send("Added to queue")
        else:
            await ctx.send("Query not found.")

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
        embeds = discordSuperUtils.generate_embeds(await MusicManager.history(self.MusicManager, ctx),
                                                   "Song History",
                                                   "Shows all played songs",
                                                   25,
                                                   string_format="Title: {}")

        page_manager = PageManager(ctx, embeds, public=True)
        await page_manager.run()

    @commands.command()
    async def skip(self, ctx, index: int = None):
        await self.MusicManager.skip(ctx, index)

    @commands.command()
    async def queue(self, ctx):
        embeds = discordSuperUtils.generate_embeds(await MusicManager.get_queue(self.MusicManager, ctx),
                                                   "Queue",
                                                   f"Now Playing: {await MusicManager.now_playing(ctx)}",
                                                   25,
                                                   string_format="Title: {}")
        page_manager = PageManager(ctx, embeds, public=True)
        await page_manager.run()


bot.add_cog(Music(bot))
bot.run("token")
