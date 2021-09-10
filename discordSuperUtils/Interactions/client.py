from __future__ import annotations

from discordSuperUtils.Base import EventManager
from .Interaction import Interaction
from .http import http
import asyncio
import inspect
import discord
from typing import (
    TYPE_CHECKING,
    Union,
    Optional
)

if TYPE_CHECKING:
    from discord.ext import commands


class SlashManager(EventManager):
    def __init__(self, bot: Union[discord.Client, commands.Bot], update_commands: Optional[bool] = True):
        super().__init__()
        self.bot = bot
        self.update_commands = update_commands
        self._ws = self.bot.ws
        self.httpsession = http()
        self.bot.add_listener(self.__dispatch_event, 'on_socket_response')
        self.commands = {}
        self.add_event(self.process_commands, 'on_interaction')

    async def process_commands(self, interaction):
        print(interaction.event)
        data = interaction.data['data']
        name = data['name']
        args = [interaction]
        args.append(arg['value'] for arg in data['options'])
        args = tuple(args)
        print(args)
        await self.commands[name](*args) # this is broken u gotta figure out how to call the command func idk i am stupid but print the event youll see

    async def __dispatch_event(self, event):
        if event['t'] == "INTERACTION_CREATE":
            await self.call_event('on_interaction', Interaction(event, self.bot))

    async def add_global_command(self, data):
        headers = {"Authorization": f"Bot gotta put token here lol idk howe to fetvch"}
        return await self.httpsession.add_global_slash_command(data=data, headers=headers,
                                                               applicationid="idk how to fetch either")

    def make_json(self, params: list):
        return [{"name": param, "description": "test choice", "type": 3} for param in params]

    def command(self):

        def inner(func):
            print(func.__name__)
            sig = inspect.signature(func)
            params = list(dict(sig.parameters).keys())
            params.pop(0)
            data = {
                "name": func.__name__,
                "description": "Slash command by DSU (beta)",
                "options": self.make_json(params)
            }
            self.commands[func.__name__] = func
            replyu = asyncio.run(self.add_global_command(data))
            print(data)
            print(replyu)
        return inner
