from discord.ext import commands
from Music import MusicManager

bot = commands.Bot(command_prefix = ".")

queue = [] # can be list or dict. Dict provides multi server functionality

music = MusicManager(queue)

@bot.event
async def on_ready():
    print(bot.user)
    
@bot.command()
async def join(ctx):
    await music.join(ctx)

@bot.command()
async def play(ctx, *, query):
    url = str(await music.search(query))
    song = await music.create_player(url=url)
    await music.queue_add(player= song, ctx=ctx)
    if not ctx.voice_client.is_playing():
        player = await music.play(ctx=ctx)
        await ctx.send(f"Now playing: {player.title}")


@bot.command()
async def pause(ctx):
    await music.pause(ctx)

@bot.command()
async def resume(ctx):
    await music.resume(ctx)

@bot.command()
async def leave(ctx):
    await music.leave(ctx)

bot.run("ODExMzMyMDA4Njc2Mjk0NjY3.YCwp0A.z71CpnNpAhom-eLuX4H3DUaaqGQ")