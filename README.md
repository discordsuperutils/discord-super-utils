<h1 align="center">discord-super-utils</h1>

<p align="center">
  <a href="#"><img src="https://img.shields.io/codefactor/grade/github/discordsuperutils/discord-super-utils?style=flat-square" /></a>
  <a href="https://discord.gg/zhwcpTBBeC"><img src="https://img.shields.io/discord/863388828734586880?logo=discord&color=blue&style=flat-square" /></a>
  <a href="https://pepy.tech/project/discordsuperutils"><img src="https://img.shields.io/pypi/dm/discordSuperUtils?color=green&style=flat-square" /></a>
  <br></br>
  <a href="https://discord-super-utils.gitbook.io/discord-super-utils/">Documentation</a>
</p>

<p align="center">
   A modern python module including many useful features that make discord bot programming extremely easy.
</p>

Features
-------------

- Modern Leveling Manager.
- Modern Music/Audio playing manager.
- Modern Database manager (SQLite, MongoDB, PostgreSQL).
- Modern Paginator.
- Modern Reaction Manager.
- Modern Economy Manager.
- Modern Image Manager (PIL).
- Modern Invite Tracker.

Installation
--------------

Installing discordSuperUtils is very easy.

```sh
python -m pip install discordSuperUtils
```

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
    print('Leveling manager is ready.', bot.user)


@LevelingManager.event()
async def on_level_up(message, member_data):
    await message.reply(f"You are now level {member_data.level}")


@bot.command()
async def rank(ctx):
    member_data = LevelingManager.get_account(ctx.author)
    await ctx.send(f'You are currently level **{member_data.level}**, with **{member_data.xp}** XP.')

bot.run("token")
```

![Leveling Manager Example](https://media.giphy.com/media/ey1Iv2HlYYLPy0bm9p/giphy.gif)

### Playing Example ### 

```py
import discordSuperUtils
from discord.ext import commands

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
                                               string_format="Title: {}")

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
                                               string_format="Title: {}")

    page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
    await page_manager.run()


bot.run("token")
```

### Database Example ###

```py
import discordSuperUtils
import pymongo
import sqlite3

mongo_database = discordSuperUtils.DatabaseManager(pymongo.MongoClient("connection string")["DATABASENAME"])
sqlite_database = discordSuperUtils.DatabaseManager(sqlite3.connect("database"))

values = sqlite_database.insert({"guild": ..., "member": ...}, "table")
print(values)
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

- **[Support Server](https://discord.gg/zhwcpTBBeC)**
- **[Documentation](https://discord-super-utils.gitbook.io/discord-super-utils/)**
