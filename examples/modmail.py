import discord
from discord.ext.commands import Bot, Context
import aiosqlite

import discordSuperUtils
from discordSuperUtils import ModMailManager

bot = Bot(command_prefix="-", intents=discord.Intents.all())
modmail = ModMailManager(bot, trigger="-modmail")


@bot.event
async def on_ready():
    print("ModMailManager is ready", bot.user)
    db = discordSuperUtils.DatabaseManager.connect(await aiosqlite.connect('db.sqlite'))
    await modmail.connect_to_database(db, ['modmail'])


@modmail.event()
async def on_modmail_request(ctx: Context):
    guilds = await modmail.get_mutual_guilds(ctx.author)
    guild = await modmail.get_modmail_guild(ctx, guilds)
    channel = await modmail.get_channel(guild)
    msg = await modmail.get_message(ctx)
    await channel.send(msg)


@bot.command()
async def setchannel(ctx, channel: discord.TextChannel):
    await modmail.set_channel(channel)
    await ctx.send(f"Channel set to {channel.mention} for {channel.guild}")


bot.run("token")
