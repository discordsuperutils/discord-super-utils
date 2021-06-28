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
    Koyashie add yo shit
```

More examples are listed in the examples folder.
