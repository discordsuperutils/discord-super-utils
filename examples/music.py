from discord.ext import commands

import discordSuperUtils
from discordSuperUtils import MusicManager

client_id = ...
client_secret = ...

bot = commands.Bot(command_prefix='-')
MusicManager = MusicManager(bot, client_id=client_id, client_secret=client_secret, inactivity_timeout=30)


@MusicManager.event()
async def on_music_error(ctx, error):
    raise error  # add your error handling here! Errors are listed in the documentation.


@MusicManager.event()
async def on_queue_end(ctx):
    print(f"The queue has ended in {ctx}")
    # You could wait and check activity, etc...


@MusicManager.event()
async def on_inactivity_disconnect(ctx):
    print(f"I have left {ctx} due to inactivity..")


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
        duration_played = await MusicManager.get_player_played_duration(ctx, player)
        # You can format it, of course.

        await ctx.send(f"Currently playing: {player}, \n"
                       f"Duration: {duration_played}/{player.duration}")


@bot.command()
async def join(ctx):
    if await MusicManager.join(ctx):
        await ctx.send("Joined Voice Channel")


@bot.command()
async def play(ctx, *, query: str):
    async with ctx.typing():
        player = await MusicManager.create_player(query)

    if player:
        await MusicManager.queue_add(player=player, ctx=ctx)

        if not await MusicManager.play(ctx):
            await ctx.send("Added to queue")

    else:
        await ctx.send("Query not found.")


@bot.command()
async def pause(ctx):
    if await MusicManager.pause(ctx):
        await ctx.send("Player paused.")


@bot.command()
async def resume(ctx):
    if await MusicManager.resume(ctx):
        await ctx.send("Player resumed.")


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
                                               string_format="Title: {}")

    page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
    await page_manager.run()


@bot.command()
async def skip(ctx, index: int = None):
    await MusicManager.skip(ctx, index)


@bot.command()
async def queue(ctx):
    embeds = discordSuperUtils.generate_embeds(await MusicManager.get_queue(ctx),
                                               "Queue",
                                               f"Now Playing: {await MusicManager.now_playing(ctx)}",
                                               25,
                                               string_format="Title: {}")

    page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
    await page_manager.run()


bot.run("token")
