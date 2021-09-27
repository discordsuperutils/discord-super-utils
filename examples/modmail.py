import discord
from discord.ext.commands import Bot, Context

import discordSuperUtils
from discordSuperUtils import ModMailManager

bot = Bot(command_prefix="-", intents=discord.Intents.all())
ModmailManager = ModMailManager(bot, trigger="-modmail")


@bot.event
async def on_ready():
    db = discordSuperUtils.DatabaseManager.connect(...)
    await ModmailManager.connect_to_database(db, ["modmail"])

    print("ModMailManager is ready.", bot.user)


@ModmailManager.event()
async def on_modmail_request(ctx: Context):
    guilds = await ModmailManager.get_mutual_guilds(ctx.author)
    guild = await ModmailManager.get_modmail_guild(ctx, guilds)
    channel = await ModmailManager.get_channel(guild)
    msg = await ModmailManager.get_message(ctx)
    await channel.send(msg)


@bot.command()
async def setchannel(ctx, channel: discord.TextChannel):
    await ModmailManager.set_channel(channel)
    await ctx.send(f"Channel set to {channel.mention} for {channel.guild}")


bot.run("token")
