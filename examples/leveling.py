import discord

import discordSuperUtils
from discord.ext import commands
import aiomysql

bot = commands.Bot(command_prefix='-')
RoleManager = discordSuperUtils.RoleManager()
LevelingManager = discordSuperUtils.LevelingManager(bot, RoleManager)


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(await aiomysql.connect(host='127.0.0.1', port=3306,
                                                                                user='ussr', password='root',
                                                                                db='testtt', loop=bot.loop))
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

    if member_data:
        await ctx.send(
            f'You are currently level **{await member_data.level()}**, with **{await member_data.xp()}** XP.')
    else:
        await ctx.send(f"I am still creating your account! please wait a few seconds.")


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
