from discord.ext import commands
from difflib import SequenceMatcher
from typing import (
    Callable,
    List,
    Union
)
import discord


class CommandHinter:
    def __init__(self, bot, generate_function: Callable[[str, List[str]], Union[discord.Embed, str]] = None):
        self.bot = bot
        self.generate_function = self.generate_embed if generate_function is None else generate_function

        self.bot.add_listener(self.__handle_hinter, "on_command_error")

    @staticmethod
    def generate_embed(invalid_command: str, suggestions: List[str]) -> discord.Embed:
        embed = discord.Embed(
            title="Invalid command!",
            description=f"**`{invalid_command}`** is invalid. Did you mean:",
            color=0x00ff00
        )

        for index, suggestion in enumerate(suggestions[:3]):
            embed.add_field(name=f"**{index + 1}.**", value=f"**`{suggestion}`**", inline=False)

        return embed

    @property
    def command_names(self):
        names = []

        for command in self.bot.commands:
            if isinstance(command, commands.Group):
                names += [command.name] + command.aliases
                for inner_command in command.commands:
                    names += [inner_command.name] + inner_command.aliases

            else:
                names += [command.name] + command.aliases

        return names

    async def __handle_hinter(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            command_similarity = {}
            command_used = ctx.message.content.lstrip(ctx.prefix)[:max([len(c) for c in self.command_names])]

            for command in self.command_names:
                command_similarity[SequenceMatcher(None, command, command_used).ratio()] = command

            generated_message = self.generate_function(command_used,
                                                       [x[1] for x in sorted(command_similarity.items(), reverse=True)])

            if isinstance(generated_message, discord.Embed):
                await ctx.send(embed=generated_message)
            elif isinstance(generated_message, str):
                await ctx.send(generated_message)
            else:
                raise TypeError("The generated message must be of type 'discord.Embed' or 'str'.")

        else:
            raise error