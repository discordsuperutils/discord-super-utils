discord-super-utils
==========

[![Downloads](https://pepy.tech/badge/discordsuperutils)](https://pepy.tech/project/discordsuperutils)
A modern python module including many useful features that make discord bot programming extremely easy.

Features
-------------

- Modern leveling manager.
- Modern Music/Audio playing manager.
- Modern Database manager (SQLite).
- Modern Paginator.
- Modern Reaction Manager.

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
from discordSuperUtils import MusicManager
from discord.ext import commands


bot = commands.Bot(command_prefix='-')
MusicManager = MusicManager(bot)


@MusicManager.event
async def on_play(ctx, player):
    await ctx.send(f"Now playing: {player.title}")

@bot.event
async def on_ready():
    print('Music manager is ready.', bot.user)



@bot.command()
async def leave(ctx):
    if await MusicManager.leave(ctx):
        await ctx.send("Left Voice Channel Lol Gang Shit")


@bot.command()
async def np(ctx):
    if player := await MusicManager.now_playing(ctx):
        await ctx.send(f"Currently playing: {player}")


@bot.command()
async def join(ctx):
    if await MusicManager.join(ctx):
        await ctx.send("Joined Voice Channel Lol Gang Shit!")


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

### Reaction Manager Example ###

```py
import sqlite3
import discord
import discordSuperUtils
from discord.ext import commands

database = discordSuperUtils.DatabaseManager(sqlite3.connect("database"))
bot = commands.Bot(command_prefix='-')
ReactionManager = discordSuperUtils.ReactionManager(database, 'reaction_roles', bot)


@ReactionManager.event()
async def on_reaction_event(guild, channel, message, member, emoji):
    """This event will be run if there isn't a role to add to the member."""

    if ...:
        print("Created ticket.")


@bot.event
async def on_ready():
    print('Reaction manager is ready.', bot.user)


@bot.command()
async def reaction(ctx, message, emoji: str, remove_on_reaction, role: discord.Role = None):
    message = await ctx.channel.fetch_message(message)

    await ReactionManager.create_reaction(ctx.guild, message, role, emoji, remove_on_reaction)


bot.run("token")
```

More examples are listed in the examples folder.

Support
--------------

- **[Support Server](https://discord.gg/zhwcpTBBeC)**
- **[Documentation](https://discord-super-utils.gitbook.io/discord-super-utils/)**
