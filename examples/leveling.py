import discordSuperUtils
import sqlite3
from discord.ext import commands


database = discordSuperUtils.DatabaseManager.connect(sqlite3.connect("database"))
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


@bot.command()
async def leaderboard(ctx):
    guild_leaderboard = LevelingManager.get_leaderboard(ctx.guild)
    formatted_leaderboard = [f"Member: {x.member}, XP: {x.xp}" for x in guild_leaderboard]

    await discordSuperUtils.PageManager(ctx, discordSuperUtils.generate_embeds(
        formatted_leaderboard,
        title="Leveling Leaderboard",
        fields=25,
        description=f"Leaderboard of {ctx.guild}"
    )).run()


bot.run("token")
