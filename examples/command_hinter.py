from typing import List

from discord.ext import commands

import discordSuperUtils


class MyCommandGenerator(discordSuperUtils.CommandResponseGenerator):
    def generate(self, invalid_command: str, suggestion: List[str]) -> str:
        # This is only an example, you can use the default generator if you want to.
        return f"Try using {suggestion[0]}"


bot = commands.Bot(command_prefix="-")
discordSuperUtils.CommandHinter(bot, MyCommandGenerator())
# Incase you want to use the default command generator, don't pass a command generator.


@bot.event
async def on_ready():
    print('Command hinter is ready.', bot.user)


@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! ping is {bot.latency * 1000}ms")


bot.run("token")
