from __future__ import annotations

import inspect
from typing import (
    Dict,
    Any,
    List,
    Callable
)

from discord.ext import commands

from .Interaction import Interaction, OptionType
from .http import HTTPClient
from ..Base import EventManager, maybe_coroutine

# discord.ext.commands is not type hinted in order to use the converters.

__all__ = ("SlashManager",)


class SlashManager(EventManager):
    """
    Represents a SlashManager that manages slash commands.
    """

    __slots__ = ("bot", "http", "commands")

    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.http = None
        self.commands = {}

        self.bot.add_listener(self.__dispatch_event, 'on_socket_response')

        self.bot.loop.create_task(self.__initialize_http())

    async def __initialize_http(self) -> None:
        """
        |coro|

        Sets the SlashManager's http object when the bot is ready.

        :return: None
        :rtype: None
        """

        await self.bot.wait_until_ready()

        self.http = HTTPClient("Bot " + self.bot.http.token)

    async def process_command(self, interaction: Interaction) -> None:
        """
        |coro|

        Processes the command.

        :param interaction: The interaction to process the command from
        :type interaction: Interaction
        :return: None
        :rtype: None
        """

        converters = {
            6: [self.bot.get_user, self.bot.fetch_user],
            7: [interaction.guild and interaction.guild.get_channel],
            8: [interaction.guild and interaction.guild.get_role]
        }

        data = interaction.data['data']
        name = data['name']

        user_arguments = []

        if 'options' in data:
            for argument in data['options']:
                arg_type = argument['type']
                if arg_type not in converters:
                    user_arguments.append(argument['value'])
                    continue

                result_fetch = argument['value']
                for converter in converters[arg_type]:
                    convert_result = await maybe_coroutine(converter, int(argument['value']))

                    if convert_result:
                        result_fetch = convert_result
                        break

                user_arguments.append(result_fetch)

        args = [interaction] + user_arguments
        await self.commands[name](*args)

    async def __dispatch_event(self, event: Dict[str, Any]) -> None:
        """
        |coro|

        Adds the on_interaction event to the SlashManager
        This function is the callback of on_socket_response.

        :param event: The socket response.
        :type event: Dict[str, Any]
        :return: None
        :rtype: None
        """

        if event['t'] == "INTERACTION_CREATE":
            interaction = Interaction(
                self.bot,
                event,
                self.http
            )

            await self.call_event('on_interaction', interaction)
            await self.process_command(interaction)

    async def add_global_command(self, payload: Dict[str, Any]) -> None:
        """
        |coro|

        Adds a global command from the payload.

        :param payload: The command options.
        :type payload: Dict[str, Any]
        :return: None
        :rtype: None
        """

        await self.bot.wait_until_ready()

        await self.http.add_slash_command(payload, self.bot.user.id)

    @staticmethod
    def parameters_to_dict(parameters) -> List[Dict[str, Any]]:
        """
        |coro|

        Converts signature parameters to their slash command JSON form.

        :param parameters: The parameters
        :return: The parameters JSON form.
        :rtype: List[Dict[str, Any]]
        """

        result_parameters = []

        for parameter in parameters:
            annotation = parameter.annotation

            result_parameters.append(
                {
                    "name": parameter.name,
                    "type": annotation.value if isinstance(annotation, OptionType) else 3,
                    "description": '-',
                    "required": True
                }
            )

        return result_parameters

    def command(self, name: str = None, description: str = "No description") -> Callable:
        """
        The command initializer decorator.

        :param name: The command name.
        :type name: str
        :param description: The command description
        :type description: str
        :return: The inner function.
        :rtype: Callable
        """

        def inner(func):
            command_name = name or func.__name__

            sig = inspect.signature(func)

            command_initializer = {
                "name": command_name,
                "type": OptionType.SUB_COMMAND.value,
                "description": description,
                "options": self.parameters_to_dict(list(sig.parameters.values())[1:])
            }

            self.commands[command_name] = func
            self.bot.loop.create_task(self.add_global_command(command_initializer))

        return inner
