from __future__ import annotations

from enum import Enum
from typing import (
    TYPE_CHECKING
)

if TYPE_CHECKING:
    from discord.ext import commands
    from .http import HTTPClient


__all__ = ("Interaction", "OptionType", "RespondType")


class RespondType(Enum):
    """Respond Types :)"""


class OptionType(Enum):
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10


class Interaction:
    """
    Represents a slash interaction.
    """

    __slots__ = ("bot", "http", "raw", "data", "args", "id", "token")

    def __init__(self,
                 bot: commands.Bot,
                 raw_interaction,
                 http: HTTPClient):
        self.bot: commands.Bot = bot
        self.http = http
        self.raw = raw_interaction
        self.data = raw_interaction['d']
        self.args = self.data['data']
        self.id = self.data['id']
        self.token = self.data['token']

    @property
    def author(self):
        """Not done."""

    @property
    def guild(self):
        """Not done."""

    @property
    def channel(self):
        """Not done."""

    def __str__(self):
        return f"<{self.__class__.__name__} guild={self.guild}, author={self.author}>"

    def __repr__(self):
        return f"<{self.__str__()}, channel={self.channel}>"

    async def reply(self, text: str) -> None:
        """
        |coro|

        Reply to an interaction.

        :param text: The text to send.
        :type text: str
        :return: The message
        :rtype: None
        """

        url = f"https://discord.com/api/v9/interactions/{self.id}/{self.token}/callback"
        payload = {
            "type": 4,
            "data": {
                "content": text
            }
        }

        await self.http.request("POST", url, payload=payload)  # Message not done.
