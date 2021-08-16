from discord.ext import commands
from difflib import SequenceMatcher
import discord


class InvalidGeneratedMessageType(Exception):
    """Raises an error when the generate_function returns an invalid type"""


class CommandHinter:
    def __init__(self, bot, generate_function):
        self.bot = bot
        self.generate_function = generate_function

        self.bot.add_listener(self.__handle_hinter, "on_command_error")

    @property
    def command_names(self):
        names = []

        for command in self.bot.commands:
            if isinstance(command, commands.Group):
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
                raise InvalidGeneratedMessageType("The generated message must be of type discord.Embed or str.")
