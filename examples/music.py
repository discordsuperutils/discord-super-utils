import discordSuperUtils
from discord.ext import commands



bot = commands.Bot(command_prefix='-')
MusicManager = discordSuperUtils.MusicManager(bot)


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
async def stop(ctx):
    ctx.voice_client.stop()

    
bot.run("token")
