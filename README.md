<h1 align="center">discordSuperUtils-splitted</h1>

<p align="center">
  <a href="https://codefactor.io/repository/github/adam757521/discordsuperutils-splitted"><img src="https://img.shields.io/codefactor/grade/github/discordsuperutils/discord-super-utils?style=flat-square" /></a>
  <a href="https://discord.gg/xzbTzhgbru"><img src="https://img.shields.io/discord/881965477189005343?logo=discord&color=blue&style=flat-square" /></a>
  <a href="https://pepy.tech/project/discordsuperutils-splitted"><img src="https://img.shields.io/pypi/dm/discordSuperUtils-splitted?color=green&style=flat-square" /></a>
  <a href="https://pypi.org/project/discordSuperUtils-splitted/"><img src="https://img.shields.io/pypi/v/discordSuperUtils-splitted?style=flat-square" /></a>
  <a href=""><img src="https://img.shields.io/pypi/l/discordSuperUtils-splitted?style=flat-square" /></a>
  <br></br>
  <a href="https://discord-super-utils.gitbook.io/discord-super-utils/">Documentation</a>
</p>

<p align="center">
   A modern python module including many useful features that make discord bot programming extremely easy.
   <br></br>
   <b>The documentation is not done. if you have any questions, feel free to ask them in our <a href="https://discord.gg/xzbTzhgbru">discord server.</a></b>
</p>

Information
-------------

I have recently left the discordSuperUtils organization because of issues with the team that wont be listed here.

Maybe this fork will merge with discordSuperUtils one day.

Features
-------------

- Very easy to use and user friendly.
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
- And many more!
(MORE COMING SOON!)

Installation
--------------

Installing discordSuperUtils-splitted is very easy.

```sh
python -m pip install discordSuperUtils-splitted
```

Examples
--------------

### Leveling Example (With Role Manager and Image Manager) ###

```py
import discord
from discord.ext import commands

import discordSuperUtils

bot = commands.Bot(command_prefix='-', intents=discord.Intents.all())
RoleManager = discordSuperUtils.RoleManager()
LevelingManager = discordSuperUtils.LevelingManager(bot, RoleManager)
ImageManager = discordSuperUtils.ImageManager()  # LevelingManager uses ImageManager to create the rank command.


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(...)
    await RoleManager.connect_to_database(database, "xp_roles")
    await LevelingManager.connect_to_database(database, "xp")

    print('Leveling manager is ready.', bot.user)


@LevelingManager.event()
async def on_level_up(message, member_data, roles):
    await message.reply(f"You are now level {await member_data.level()}" + (f", you have received the {roles[0]}"
                                                                            f" role." if roles else ""))


@bot.command()
async def rank(ctx):
    member_data = await LevelingManager.get_account(ctx.author)

    if not member_data:
        await ctx.send(f"I am still creating your account! please wait a few seconds.")
        return

    guild_leaderboard = await LevelingManager.get_leaderboard(ctx.guild)
    member = [x for x in guild_leaderboard if x.member == ctx.author.id]

    image = await ImageManager.create_leveling_profile(ctx.author,
                                                       member_data,
                                                       discordSuperUtils.Backgrounds.GALAXY,
                                                       (255, 255, 255),
                                                       guild_leaderboard.index(member[0]) + 1 if member else -1,
                                                       outline=True)
    await ctx.send(file=image)


@bot.command()
async def set_roles(ctx, *roles: discord.Role):
    await RoleManager.set_roles(ctx.guild, {"roles": roles})


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

More examples are listed in the examples folder.

Known Issues
--------------

- Removing an animated emoji wont be recognized as a reaction role, as it shows up as not animated for some reason, breaking the reaction matcher. (Discord API Related)
- Spotify queueing is very slow. 

Support
--------------

- **[Support Server](https://discord.gg/xzbTzhgbru)**
- **[Documentation](https://discord-super-utils.gitbook.io/discord-super-utils/)**
