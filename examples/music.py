import discordSuperUtils
from discord.ext import commands
import discord

bot = commands.Bot(command_prefix='-')
MusicManager = discordSuperUtils.MusicManager(bot)


@MusicManager.event()
async def on_music_error(ctx, error):
    raise error  # add your error handling here! Errors are listed in the documentation.


@MusicManager.event()
async def on_play(ctx, player):
    await ctx.send(f"Playing {player}")


@bot.event
async def on_ready():
    print('Music manager is ready.', bot.user)


@bot.command()
async def leave(ctx):
    if await MusicManager.leave(ctx):
        await ctx.send("Left Voice Channel")


@bot.command()
async def np(ctx):
    if player := await MusicManager.now_playing(ctx):
        await ctx.send(f"Currently playing: {player}")


@bot.command()
async def join(ctx):
    if await MusicManager.join(ctx):
        await ctx.send("Joined Voice Channel")


@bot.command()
async def play(ctx, *, query: str):
    player = await MusicManager.create_player(query)
    await MusicManager.queue_add(player=player, ctx=ctx)

    if not await MusicManager.play(ctx):
        await ctx.send("Added to queue")


@bot.command()
async def volume(ctx, volume: int):
    await MusicManager.volume(ctx, volume)


@bot.command()
async def loop(ctx):
    is_loop = await MusicManager.loop(ctx)
    await ctx.send(f"Looping toggled to {is_loop}")


@bot.command()
async def queueloop(ctx):
    is_loop = await MusicManager.queueloop(ctx)
    await ctx.send(f"Queue looping toggled to {is_loop}")


@bot.command()
async def history(ctx):
    embeds = discordSuperUtils.generate_embeds(await MusicManager.history(ctx),
                                               "Song History",
                                               "Shows all played songs",
                                               25,
                                               "Title: {}")

    page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
    await page_manager.run()


@bot.command()
async def skip(ctx, index: int = None):
    await MusicManager.skip(ctx, index)


@bot.command()
async def queue(ctx):
    embeds = discordSuperUtils.generate_embeds(MusicManager.get_queue(ctx),
                                               "Queue",
                                               f"Now Playing: {await MusicManager.now_playing(ctx)}",
                                               25,
                                               "Title: {}")

    page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
    await page_manager.run()


bot.run("token")
