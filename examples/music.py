import discordSuperUtils
from discord.ext import commands
import discord

bot = commands.Bot(command_prefix='-')
MusicManager = discordSuperUtils.MusicManager(bot)


@MusicManager.event()
async def on_music_error(ctx, error):
    raise error


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
async def skip(ctx):
    await MusicManager.skip(ctx)

@bot.command()
async def queue(ctx):
    embed = discord.Embed(title="Queue", description=f" Now Playing: {await MusicManager.now_playing(ctx)}")
    queue = await MusicManager.fetch_queue(ctx)
    if len(queue) < 27:
        for song in queue:
            embed.add_field(name=f"{queue.index(song) + 1}", value=f"{song}", inline=False)
    await ctx.send(embed=embed)




bot.run("ODExMzMyMDA4Njc2Mjk0NjY3.YCwp0A.IXel_tk8lEU4mJ15Tv8W-c4iwIc")
