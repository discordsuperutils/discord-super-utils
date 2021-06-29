discord-super-utils
==========

A modern python module including many useful features that make discord bot programming extremely easy.

Features
-------------

- Modern leveling manager.
- Modern Music/Audio playing manager.
- Modern Database manager (SQLite).
- Modern Paginator.

Examples
--------------

### Leveling Example ###

```py
import discordSuperUtils
import sqlite3
from discord.ext import commands


database = discordSuperUtils.DatabaseManager(sqlite3.connect("database"))
bot = commands.Bot(command_prefix='-')
LevelingManager = discordSuperUtils.LevelingManager(database, 'xp', bot)


@bot.event
async def on_ready():
    print('Leveling manager is ready.')


@LevelingManager.event()
async def on_level_up(message, member_data):
    await message.reply(f"You are now level {member_data['rank']}")


@bot.command()
async def rank(ctx):
    member_data = LevelingManager.get_member(ctx.author)
    await ctx.send(f'You are currently level **{member_data["rank"]}**, with **{member_data["xp"]}** XP.')

bot.run("token")
```

![Leveling Manager Example](https://media.giphy.com/media/ey1Iv2HlYYLPy0bm9p/giphy.gif)

### Playing Example ### 

```py
from discord.ext import commands
from discordSuperUtils import MusicManager

bot = commands.Bot(command_prefix = ".")

queue = []  # can be list or dict. Dict provides multi server functionality

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

bot.run("token")
```

### Database Example ###

```py
import discordSuperUtils
import sqlite3


database = discordSuperUtils.DatabaseManager(sqlite3.connect("database"))
values = database.select(keys=['guild'], table_name='xp', checks=[{'guild': 1}], fetchall=True) 
```

### Paginator Example ###  

```py
import discordSuperUtils
from discord.ext import commands
import discord


bot = commands.Bot(command_prefix='-')


@bot.event
async def on_ready():
    print('Page manager is ready.', bot.user)


@bot.command()
async def paginator(ctx):
    messages = [
        discord.Embed(
            title='Data (1/2)',
            description="Hello world"
        ),
        "Hello world"
    ]

    await discordSuperUtils.PageManager(ctx, messages).run()


bot.run("token")
```

More examples are listed in the examples folder.

Support
--------------

- **[Support Server](https://discord.gg/TttN2qc7Tg)**
- **[Documentation](https://discord-super-utils.gitbook.io/discord-super-utils/)**
