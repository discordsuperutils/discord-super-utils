discord-super-utils
==========

A modern python module including many useful features that make discord bot programming extremely easy.

Features
-------------

- Modern leveling manager.
- Modern Music/Audio playing manager.
- Database manager.

Examples
--------------

### Leveling Example ###

```py
    import DisCock
    import sqlite3
    from discord.ext import commands


    database = DisCock.Database(sqlite3.connect("database"))
    bot = commands.Bot(command_prefix='-')
    LevelingManager = DisCock.LevelingManager(database, 'xp', bot)


    @bot.event
    async def on_ready():
        print('Leveling manager is ready.')


    @LevelingManager.event()
    async def on_level_up(message, member_data):
        await message.reply(f"You are now level {member_data['rank']}")


    @bot.command()
    async def rank(ctx):
        member_data = LevelingManager.get_member(ctx.guild, ctx.author)
        await ctx.send(f'You are currently level **{member_data["rank"]}**, with **{member_data["xp"]} XP.')

    bot.run("token")
```

### Playing Example ### 

```py
from discord.ext import commands
from discord-super-utils.Music import  Player, music, search

bot = commands.Bot(command_prefix = ".")

queue = []

def check_queue(ctx):
    queue.pop(0)
    try:
        player = queue[0]
    except IndexError:
        return
    asyncio.run_coroutine_threadsafe(ctx.send( f"Now playing: {player.title}"), bot.loop)    #await can be used but the function isnt async
    asyncio.run_coroutine_threadsafe(Player.play(ctx=ctx, player=player ,after= lambda x :check_queue(ctx)), bot.loop)

@bot.event
async def on_ready():
    print(bot.user)
    
@bot.command()
async def join(ctx):
    await Player.join(ctx)

@bot.command()
async def play(ctx,*, query):
    url = await search(query=query)
    song = await music.create_player(url=url)
    queue.append(song)
    if not ctx.voice_client.is_playing():
        player = queue[0]
        await ctx.send(f"Now playing: {player.title}")
        await Player.play(ctx=ctx, player=player ,after= lambda x :check_queue(ctx))

@bot.command()
async def pause(ctx):
    await Player.pause(ctx)

@bot.command()
async def resume(ctx):
    await Player.resume(ctx)

@bot.command()
async def leave(ctx):
    await Player.leave(ctx)
    
bot.run('token')
```

More examples are listed in the examples folder.
