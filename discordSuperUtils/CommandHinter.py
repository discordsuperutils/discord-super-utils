from difflib import SequenceMatcher
from typing import (
    List,
    Union
)
from abc import ABC, abstractmethod
import inspect

import discord
from discord.ext import commands


class CommandResponseGenerator(ABC):
    @abstractmethod
    def generate(self, invalid_command: str, suggestions: List[str]) -> Union[str, discord.Embed]:
        pass


class DefaultResponseGenerator(CommandResponseGenerator):
    def generate(self, invalid_command: str, suggestions: List[str]) -> discord.Embed:
        embed = discord.Embed(
            title="Invalid command!",
            description=f"**`{invalid_command}`** is invalid. Did you mean:",
            color=0x00ff00
        )

        for index, suggestion in enumerate(suggestions[:3]):
            embed.add_field(name=f"**{index + 1}.**", value=f"**`{suggestion}`**", inline=False)

        return embed


class InvalidGenerator(Exception):
    def __init__(self, generator):
        self.generator = generator
        super().__init__(f"Generator of type {type(self.generator)!r} is not supported.")


class CommandHinter:
    def __init__(self,
                 bot: commands.Bot,
                 generator=None):
        self.bot = bot
        self.generator = DefaultResponseGenerator if generator is None else generator

        self.bot.add_listener(self.__handle_hinter, "on_command_error")

    @property
    def command_names(self) -> List[str]:
        names = []

        for command in self.bot.commands:
            if isinstance(command, commands.Group):
                names += [command.name] + command.aliases
                for inner_command in command.commands:
                    names += [inner_command.name] + inner_command.aliases

            else:
                names += [command.name] + command.aliases

        return names

    def _generate_message(self, command_used: str, suggestions: List[str]) -> Union[discord.Embed, str]:
        if inspect.isclass(self.generator) and issubclass(self.generator, CommandResponseGenerator):
            if inspect.ismethod(self.generator.generate):
                return self.generator.generate(command_used, suggestions)
            else:
                return self.generator().generate(command_used, suggestions)
        elif isinstance(self.generator, CommandResponseGenerator):
            return self.generator.generate(command_used, suggestions)
        else:
            raise InvalidGenerator(self.generator)

    async def __handle_hinter(self, ctx: commands.Context, error) -> None:
        if isinstance(error, commands.CommandNotFound):
            command_similarity = {}
            command_used = ctx.message.content.lstrip(ctx.prefix)[:max([len(c) for c in self.command_names])]

            for command in self.command_names:
                command_similarity[SequenceMatcher(None, command, command_used).ratio()] = command

            generated_message = self._generate_message(command_used,
                                                       [x[1] for x in sorted(command_similarity.items(), reverse=True)])

            if isinstance(generated_message, discord.Embed):
                await ctx.send(embed=generated_message)
            elif isinstance(generated_message, str):
                await ctx.send(generated_message)
            else:
                raise TypeError("The generated message must be of type 'discord.Embed' or 'str'.")

        else:
            raise error