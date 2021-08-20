<h1 align="center">discord-super-utils</h1>

<p align="center">
  <a href="#"><img src="https://img.shields.io/codefactor/grade/github/discordsuperutils/discord-super-utils?style=flat-square" /></a>
  <a href="https://discord.gg/zhwcpTBBeC"><img src="https://img.shields.io/discord/863388828734586880?logo=discord&color=blue&style=flat-square" /></a>
  <a href="https://pepy.tech/project/discordsuperutils"><img src="https://img.shields.io/pypi/dm/discordSuperUtils?color=green&style=flat-square" /></a>
  <a href="https://pypi.org/project/discordSuperUtils/"><img src="https://img.shields.io/pypi/v/discordSuperUtils?style=flat-square" /></a>
  <a href=""><img src="https://img.shields.io/pypi/l/discordSuperUtils?style=flat-square" /></a>
  <br></br>
  <a href="https://discord-super-utils.gitbook.io/discord-super-utils/">Documentation</a>
</p>

<p align="center">
   A modern python module including many useful features that make discord bot programming extremely easy.
   <br></br>
   <b>The documentation is not done. if you have any questions, feel free to ask them in our <a href="https://discord.gg/zhwcpTBBeC">discord server.</a></b>
</p>

Features
-------------

- Very easy to use and user friendly.
- Modern Leveling Manager.
- Modern Music/Audio playing manager.
- Modern Async Database Manager (SQLite, MongoDB, PostgreSQL).
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
from discord.ext import commands

bot = commands.Bot(command_prefix='-')
LevelingManager = discordSuperUtils.LevelingManager(bot)


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(...)
    await LevelingManager.connect_to_database(database, "xp")

    print('Leveling manager is ready.', bot.user)


@LevelingManager.event()
async def on_level_up(message, member_data):
    await message.reply(f"You are now level {member_data.level}")


@bot.command()
async def rank(ctx):
    member_data = await LevelingManager.get_account(ctx.author)
    await ctx.send(f'You are currently level **{await member_data.level()}**, with **{await member_data.xp()}** XP.')


@bot.command()
async def leaderboard(ctx):
    guild_leaderboard = await LevelingManager.get_leaderboard(ctx.guild)
    formatted_leaderboard = [f"Member: {x.member}, XP: {await x.xp()}" for x in guild_leaderboard]

    await discordSuperUtils.PageManager(ctx, discordSuperUtils.generate_embeds(
        formatted_leaderboard,
        title="Leveling Leaderboard",
        fields=25,
        description=f"Leaderboard of {ctx.guild}"
    )).run()


bot.run("token")
```

![Leveling Manager Example](https://media.giphy.com/media/ey1Iv2HlYYLPy0bm9p/giphy.gif)

### Playing Example ### 

```py
import discordSuperUtils
from discord.ext import commands
from discordSuperUtils import MusicManager

client_id = ...
client_secret = ...

bot = commands.Bot(command_prefix='-')
MusicManager = MusicManager(bot, client_id=client_id, client_secret=client_secret)


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
    if player:
        await MusicManager.queue_add(player=player, ctx=ctx)

        if not await MusicManager.play(ctx):
            await ctx.send("Added to queue")

    else:
        await ctx.send("Query not found.")


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
```
![MusicManager Example](https://media.giphy.com/media/SF6K0zIVHl6RCQ0Aqk/giphy.gif)

### Database Example ###

```py
import discordSuperUtils
import aiosqlite
from motor import motor_asyncio
import asyncio


async def database_test():
    mongo_database = discordSuperUtils.DatabaseManager.connect(motor_asyncio.AsyncIOMotorClient("con-string")['name'])
    # Replace 'con-string' by the MongoDB connection string and 'name' by the database name you want to use.

    postgre_database = discordSuperUtils.DatabaseManager.connect(await discordSuperUtils.create_postgre("con-string"))
    # Replace 'con-string' by the PostrgeSQL connection string.
    # PostgreSQL connection string example:
    # "dbname=name user=postgres password=xxx host=host" host is not required.

    sqlite_database = discordSuperUtils.DatabaseManager.connect(await aiosqlite.connect('path'))
    # Replace 'path' by the SQLite database path. (must be on your computer)

    await sqlite_database.insert('economy', {'guild': ..., 'member': ..., 'currency': ..., 'bank': ...})

    await sqlite_database.close()  # not required.


loop = asyncio.get_event_loop()
loop.run_until_complete(database_test())
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

Known Issues
--------------

- Removing an animated emoji wont be recognized as a reaction role, as it shows up as not animated for some reason, breaking the reaction matcher.
- Spotify queueing is very slow. 
- Our event decorators do not work in Cogs. (Can be called manually, we are working on a fix currently)

Support
--------------

- **[Support Server](https://discord.gg/zhwcpTBBeC)**
- **[Documentation](https://discord-super-utils.gitbook.io/discord-super-utils/)**
