<h1 align="center">discord-super-utils</h1>

<p align="center">
  <a href="https://codefactor.io/repository/github/discordsuperutils/discord-super-utils/"><img src="https://img.shields.io/codefactor/grade/github/discordsuperutils/discord-super-utils?style=flat-square" /></a>
  <a href="https://discord.gg/zhwcpTBBeC"><img src="https://img.shields.io/discord/863388828734586880?logo=discord&color=blue&style=flat-square" /></a>
  <a href="https://pepy.tech/project/discordsuperutils"><img src="https://img.shields.io/pypi/dm/discordSuperUtils?color=green&style=flat-square" /></a>
  <a href="https://pypi.org/project/discordSuperUtils/"><img src="https://img.shields.io/pypi/v/discordSuperUtils?style=flat-square" /></a>
  <a href=""><img src="https://img.shields.io/pypi/l/discordSuperUtils?style=flat-square" /></a>
  <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square">
    <br/>
  <a href="https://discord-super-utils.gitbook.io/discord-super-utils/">Documentation</a>
  <a href="https://discordsuperutils.readthedocs.io/en/latest/">Secondary Documentation</a>
</p>

<p align="center">
   A modern python module including many useful features that make discord bot programming extremely easy.
    <br/>
   <b>The documentation is not done. if you have any questions, feel free to ask them in our <a href="https://discord.gg/zhwcpTBBeC">discord server.</a></b>
</p>

Features
-------------


- Very easy to use and user-friendly.
- Object Oriented.
- Modern Leveling Manager.
- Modern Music/Audio playing manager.
- Modern Async Database Manager (SQLite, MongoDB, PostgreSQL, MySQL, MariaDB).
- Modern Paginator.
- Modern Reaction Manager.
- Modern Economy Manager.
- Modern Image Manager (PIL).
- Modern Invite Tracker.
- Modern Command Hinter.
- Modern FiveM Server Parser.
- Modern Birthday Manager.
- Modern Prefix Manager.
- Includes easy to use convertors.
- Modern spotify client that is optimized for player fetching.
- Modern Punishment Manager (Kick, Ban, Infractions, Mutes)
- Modern Template Manager.
- Modern CogManager that supports usage of managers in discord cogs.
- Modern MessageFilter and AntiSpam.
- Modern youtube client that is optimized for player fetching.
- And many more!
(MORE COMING SOON!)

Installation
--------------

Installing discordSuperUtils is very easy.

```sh
python -m pip install discordSuperUtils
```

Examples
--------------

### Leveling Example (With Role Manager) ###

```py
import discord
from discord.ext import commands

import discordSuperUtils

bot = commands.Bot(command_prefix="-", intents=discord.Intents.all())
LevelingManager = discordSuperUtils.LevelingManager(bot, award_role=True)
ImageManager = (
    discordSuperUtils.ImageManager()
)  # LevelingManager uses ImageManager to create the rank command.


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(...)
    await LevelingManager.connect_to_database(database, ["xp", "roles", "role_list"])

    print("Leveling manager is ready.", bot.user)


@LevelingManager.event()
async def on_level_up(message, member_data, roles):
    await message.reply(
        f"You are now level {await member_data.level()}"
        + (f", you have received the {roles[0]}" f" role." if roles else "")
    )


@bot.command()
async def rank(ctx):
    member_data = await LevelingManager.get_account(ctx.author)

    if not member_data:
        await ctx.send(f"I am still creating your account! please wait a few seconds.")
        return

    guild_leaderboard = await LevelingManager.get_leaderboard(ctx.guild)
    member = [x for x in guild_leaderboard if x.member == ctx.author.id]

    image = await ImageManager.create_leveling_profile(
        ctx.author,
        member_data,
        discordSuperUtils.Backgrounds.GALAXY,
        (127, 255, 0),
        guild_leaderboard.index(member[0]) + 1 if member else -1,
        outline=5,
    )
    await ctx.send(file=image)


@bot.command()
async def set_roles(ctx, interval: int, *roles: discord.Role):
    await LevelingManager.set_interval(ctx.guild, interval)
    await LevelingManager.set_roles(ctx.guild, roles)

    await ctx.send(
        f"Successfully set the interval to {interval} and role list to {', '.join(role.name for role in roles)}"
    )


@bot.command()
async def leaderboard(ctx):
    guild_leaderboard = await LevelingManager.get_leaderboard(ctx.guild)
    formatted_leaderboard = [
        f"Member: {x.member}, XP: {await x.xp()}" for x in guild_leaderboard
    ]

    await discordSuperUtils.PageManager(
        ctx,
        discordSuperUtils.generate_embeds(
            formatted_leaderboard,
            title="Leveling Leaderboard",
            fields=25,
            description=f"Leaderboard of {ctx.guild}",
        ),
    ).run()


bot.run("token")
```

![Leveling Manager Example](https://media.giphy.com/media/ey1Iv2HlYYLPy0bm9p/giphy.gif)

### Playing Example ### 

```py
from discord.ext import commands

import discordSuperUtils
from discordSuperUtils import MusicManager
import discord

client_id = ""
client_secret = ""

bot = commands.Bot(command_prefix="-")
MusicManager = MusicManager(
    bot, spotify_support=True, client_id=client_id, client_secret=client_secret
)


# MusicManager = MusicManager(bot, client_id=client_id,
#                                   client_secret=client_secret, spotify_support=True)

# if using spotify support use this instead ^^^


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
    print("Music manager is ready.", bot.user)


@bot.command()
async def leave(ctx):
    if await MusicManager.leave(ctx):
        await ctx.send("Left Voice Channel")


@bot.command()
async def np(ctx):
    if player := await MusicManager.now_playing(ctx):
        duration_played = await MusicManager.get_player_played_duration(ctx, player)
        # You can format it, of course.

        await ctx.send(
            f"Currently playing: {player}, \n"
            f"Duration: {duration_played}/{player.duration}"
        )


@bot.command()
async def join(ctx):
    if await MusicManager.join(ctx):
        await ctx.send("Joined Voice Channel")


@bot.command()
async def play(ctx, *, query: str):
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        await MusicManager.join(ctx)

    async with ctx.typing():
        players = await MusicManager.create_player(query, ctx.author)

    if players:
        if await MusicManager.queue_add(
            players=players, ctx=ctx
        ) and not await MusicManager.play(ctx):
            await ctx.send("Added to queue")

    else:
        await ctx.send("Query not found.")


@bot.command()
async def lyrics(ctx, query: str = None):
    if response := await MusicManager.lyrics(ctx, query):
        title, author, query_lyrics = response

        splitted = query_lyrics.split("\n")
        res = []
        current = ""
        for i, split in enumerate(splitted):
            if len(splitted) <= i + 1 or len(current) + len(splitted[i + 1]) > 1024:
                res.append(current)
                current = ""
                continue
            current += split + "\n"

        page_manager = discordSuperUtils.PageManager(
            ctx,
            [
                discord.Embed(
                    title=f"Lyrics for '{title}' by '{author}', (Page {i + 1}/{len(res)})",
                    description=x,
                )
                for i, x in enumerate(res)
            ],
            public=True,
        )
        await page_manager.run()
    else:
        await ctx.send("No lyrics found.")


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
async def shuffle(ctx):
    is_shuffle = await MusicManager.shuffle(ctx)
    await ctx.send(f"Shuffle toggled to {is_shuffle}")


@bot.command()
async def autoplay(ctx):
    is_autoplay = await MusicManager.autoplay(ctx)
    await ctx.send(f"Autoplay toggled to {is_autoplay}")


@bot.command()
async def queueloop(ctx):
    is_loop = await MusicManager.queueloop(ctx)
    await ctx.send(f"Queue looping toggled to {is_loop}")


@bot.command()
async def history(ctx):
    formatted_history = [
        f"Title: '{x.title}'\nRequester: {x.requester.mention}"
        for x in (await MusicManager.get_queue(ctx)).history
    ]

    embeds = discordSuperUtils.generate_embeds(
        formatted_history,
        "Song History",
        "Shows all played songs",
        25,
        string_format="{}",
    )

    page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
    await page_manager.run()


@bot.command()
async def skip(ctx, index: int = None):
    await MusicManager.skip(ctx, index)


@bot.command()
async def queue(ctx):
    formatted_queue = [
        f"Title: '{x.title}\nRequester: {x.requester.mention}"
        for x in (await MusicManager.get_queue(ctx)).queue
    ]

    embeds = discordSuperUtils.generate_embeds(
        formatted_queue,
        "Queue",
        f"Now Playing: {await MusicManager.now_playing(ctx)}",
        25,
        string_format="{}",
    )

    page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
    await page_manager.run()


@bot.command()
async def ls(ctx):
    if queue := await MusicManager.get_queue(ctx):
        loop = queue.loop
        loop_status = None

        if loop == discordSuperUtils.Loops.LOOP:
            loop_status = "Looping enabled."

        elif loop == discordSuperUtils.Loops.QUEUE_LOOP:
            loop_status = "Queue looping enabled."

        elif loop == discordSuperUtils.Loops.NO_LOOP:
            loop_status = "No loop enabled."

        if loop_status:
            await ctx.send(loop_status)


bot.run("token")
```

![MusicManager Example](https://media.giphy.com/media/SF6K0zIVHl6RCQ0Aqk/giphy.gif)

More examples are listed in the examples folder.

Known Issues
--------------

- Removing an animated emoji wont be recognized as a reaction role, as it shows up as not animated for some reason, breaking the reaction matcher. (Discord API Related)

Support
--------------

- **[Support Server](https://discord.gg/zhwcpTBBeC)**
- **[Documentation](https://discord-super-utils.gitbook.io/discord-super-utils/)**
