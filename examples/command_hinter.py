from typing import List

import discordSuperUtils
from discord.ext import commands
import discord


def generate_embed(invalid_command: str, suggestions: List[str]) -> discord.Embed:
    embed = discord.Embed(
        title="Invalid command!",
        description=f"**`{invalid_command}`** is invalid. Did you mean:",
        color=0x00ff00
    )

    for index, suggestion in enumerate(suggestions[:3]):
        embed.add_field(name=f"**{index + 1}.**", value=f"**`{suggestion}`**", inline=False)

    return embed


bot = commands.Bot(command_prefix="-")
InviteTracker = discordSuperUtils.CommandHinter(bot, generate_embed)


@bot.event
async def on_ready():
    print('Command hinter is ready.', bot.user)


@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! ping is {bot.latency}ms")


bot.run("token")
