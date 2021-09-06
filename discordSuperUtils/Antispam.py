from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import timedelta
from difflib import SequenceMatcher
from typing import (
    TYPE_CHECKING,
    List,
    Union,
    Any,
    Iterable
)

import discord

from .Base import EventManager, get_generator_response
from .Punishments import get_relevant_punishment

if TYPE_CHECKING:
    from discord.ext import commands
    from .Punishments import Punishment

__all__ = ("SpamManager", "SpamDetectionGenerator", "DefaultSpamDetectionGenerator")


class SpamDetectionGenerator(ABC):
    """
    Represents a SpamManager that filters messages to find spam.
    """

    __slots__ = ()

    @abstractmethod
    def generate(self, last_messages: List[discord.Message]) -> Union[bool, Any]:
        """
        This function is an abstract method.
        The generate function of the generator.

        :param last_messages: The last messages sent (5 is max).
        :type last_messages: List[discord.Message]
        :return: A boolean representing if the message is spam.
        :rtype: Union[bool, Any]
        """

        pass


class DefaultSpamDetectionGenerator(SpamDetectionGenerator):
    def generate(self, last_messages: List[discord.Message]) -> Union[bool, Any]:
        """
        This function processes the last messages and returns a bool representing if the message is spam.
        Returns false automatically if the member is an administrator.

        :param last_messages: The last messages (5 is max).
        :type last_messages: List[discord.Message]
        :return: A boolean representing if the message is spam.
        :rtype: Union[bool, Any]
        """

        member = last_messages[0].author
        if member.guild_permissions.administrator:
            return False

        return SpamManager.get_messages_similarity([message.content for message in last_messages]) > 0.70


class SpamManager(EventManager):
    """
    Represents a SpamManager which detects spam.
    """

    __slots__ = ("bot", "generator", "punishments", "_spam_cache", "_last_messages")

    def __init__(self,
                 bot: commands.Bot,
                 generator: SpamDetectionGenerator = None,
                 wipe_cache_delay: timedelta = timedelta(minutes=5)):
        super().__init__()
        self.bot = bot
        self.generator = generator if generator is not None else DefaultSpamDetectionGenerator
        self.wipe_cache_delay = wipe_cache_delay
        self.punishments = []
        self._spam_cache = {}
        self._last_messages = {}

        self.bot.loop.create_task(self.__wipe_cache())
        self.bot.add_listener(self.__handle_messages, "on_message")
        self.bot.add_listener(self.__handle_messages, "on_message_edit")

    async def __wipe_cache(self):
        """
        This function is responsible for wiping the member cache.

        :return:
        """

        while not self.bot.is_closed():
            await asyncio.sleep(self.wipe_cache_delay.total_seconds())

            self._spam_cache = {}

    @staticmethod
    def get_messages_similarity(messages: Iterable[str]) -> float:
        """
        Gets the similarity between messages.

        :param messages: Messages to compare.
        :type messages: Iterable[str]
        :rtype: float
        :return: The similarity between messages (0-1)
        """

        results = []

        for i, message in enumerate(messages):
            for second_index, second_message in enumerate(messages):
                if i != second_index:
                    results.append(SequenceMatcher(None, message, second_message).ratio())

        return sum(results) / len(results) if results else 0

    def add_punishments(self, punishments: List[Punishment]) -> None:
        self.punishments = punishments

    async def __handle_messages(self, message, edited_message=None):
        """
        This function is the main logic of the SpamManager
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

        member_last_messages = self._last_messages.setdefault(message.guild.id, {}).get(message.author.id, [])

        member_last_messages.append(message)
        member_last_messages = member_last_messages[-5:]

        self._last_messages[message.guild.id][message.author.id] = member_last_messages

        if len(member_last_messages) <= 3 or not get_generator_response(self.generator, SpamDetectionGenerator, member_last_messages):
            return

        # member_warnings are the number of times the member has spammed.
        member_warnings = self._spam_cache.setdefault(message.guild.id, {}).get(message.author.id, 0) + 1
        self._spam_cache[message.guild.id][message.author.id] = member_warnings

        await self.call_event("on_message_spam", member_last_messages, member_warnings)

        if punishment := get_relevant_punishment(self.punishments, member_warnings):
            await punishment.punishment_manager.punish(message, message.author, punishment)
