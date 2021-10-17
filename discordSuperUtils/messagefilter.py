from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import TYPE_CHECKING, Union, Any, List

from .base import get_generator_response, EventManager, CacheBased
from .punishments import get_relevant_punishment

if TYPE_CHECKING:
    from discord.ext import commands
    import discord
    from .punishments import Punishment

__all__ = (
    "MessageFilter",
    "MessageResponseGenerator",
    "DefaultMessageResponseGenerator",
)


class MessageResponseGenerator(ABC):
    """
    Represents a URL response generator that filters messages and checks if they contain URLs or anything
    inappropriate.
    """

    __slots__ = ()

    @abstractmethod
    def generate(self, message: discord.Message) -> Union[bool, Any]:
        """
        This function is an abstract method.
        The generate function of the generator.

        :param message: The message to filter.
        :type message: discord.Message
        :return: A boolean representing if the message contains inappropriate content.
        :rtype: Union[bool, Any]
        """


class DefaultMessageResponseGenerator(MessageResponseGenerator):
    URL_RE = re.compile(
        r"(https?://(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9]["
        r"a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?://(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,"
        r"}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"
    )
    DISCORD_INVITE_RE = re.compile(
        r"(?:(?:http|https)://)?(?:www.)?(?:disco|discord|discordapp).("
        r"?:com|gg|io|li|me|net|org)(?:/(?:invite))?/([a-z0-9-.]+)"
    )

    def generate(self, message: discord.Message) -> Union[bool, Any]:
        if message.author.guild_permissions.administrator:
            return False

        return self.URL_RE.match(message.content) or self.DISCORD_INVITE_RE.match(
            message.content
        )


class MessageFilter(EventManager, CacheBased):
    """
    Represents a discordSuperUtils message filter that filters messages and finds inappropriate content.
    """

    __slots__ = ("bot", "generator", "punishments")

    def __init__(
        self,
        bot: commands.Bot,
        generator: MessageResponseGenerator = None,
        delete_message: bool = True,
        wipe_cache_delay: timedelta = timedelta(minutes=5),
    ):
        CacheBased.__init__(self, bot, wipe_cache_delay)
        EventManager.__init__(self)

        self.generator = (
            generator if generator is not None else DefaultMessageResponseGenerator
        )
        self.delete_message = delete_message
        self.punishments = []

        self.bot.add_listener(self.__handle_messages, "on_message")
        self.bot.add_listener(self.__handle_messages, "on_message_edit")

    def add_punishments(self, punishments: List[Punishment]) -> None:
        self.punishments = punishments

    async def __handle_messages(self, message, edited_message=None):
        """
        This function is the main logic of the MessageFilter,
        Handled events: on_message, on_message_edit

        :param message: The on_message message passed by the event.
        :type message: discord.Message
        :param edited_message: The edited messages passed by the on_message_edit event, this function will use this
        incase it is not None.
        :type edited_message: discord.Message
        :return:
        """

        message = edited_message or message

        if not message.guild or message.author.bot:
            return

        if not get_generator_response(
            self.generator, MessageResponseGenerator, message
        ):
            return

        if self.delete_message:
            await message.delete()

        member_warnings = (
            self._cache.setdefault(message.guild.id, {}).get(message.author.id, 0) + 1
        )
        self._cache[message.guild.id][message.author.id] = member_warnings

        await self.call_event("on_inappropriate_message", message, member_warnings)

        if punishment := get_relevant_punishment(self.punishments, member_warnings):
            await punishment.punishment_manager.punish(
                message, message.author, punishment
            )
