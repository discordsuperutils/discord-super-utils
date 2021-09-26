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
    member = [x for x in guild_leaderboard if x.member == ctx.author]

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
