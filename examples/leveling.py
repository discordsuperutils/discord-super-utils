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
    await message.reply(f"You are now level {member_data['rank']}")


@bot.command()
async def rank(ctx):
    member_data = LevelingManager.get_account(ctx.author)
    await ctx.send(f'You are currently level **{member_data["rank"]}**, with **{member_data["xp"]}** XP.')

bot.run("token")
