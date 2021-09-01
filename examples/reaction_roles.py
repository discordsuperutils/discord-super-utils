import discord
from discord.ext import commands

import discordSuperUtils

bot = commands.Bot(command_prefix='-', intents=discord.Intents.all())
ReactionManager = discordSuperUtils.ReactionManager(bot)


@ReactionManager.event()
async def on_reaction_event(guild, channel, message, member, emoji):
    """This event will be run if there isn't a role to add to the member."""

    if ...:
        print("Created ticket.")


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(...)
    await ReactionManager.connect_to_database(database, ["reaction_roles"])

    print('Reaction manager is ready.', bot.user)


@bot.command()
async def reaction(ctx, message, emoji: str, remove_on_reaction, role: discord.Role = None):
    message = await ctx.channel.fetch_message(message)

    await ReactionManager.create_reaction(ctx.guild, message, role, emoji, remove_on_reaction)


bot.run("token")
