from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, List, Union, Any, Iterable

import discord

from .base import EventManager, get_generator_response, CacheBased
from .punishments import get_relevant_punishment

if TYPE_CHECKING:
    from discord.ext import commands
    from .punishments import Punishment

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
        member = last_messages[0].author
        if member.guild_permissions.administrator:
            return False

        return (
            SpamManager.get_messages_similarity(
                [message.content for message in last_messages]
            )
            > 0.70
        )


class SpamManager(CacheBased, EventManager):
    """
    Represents a SpamManager which detects spam.
    """

    __slots__ = ("bot", "generator", "punishments", "_last_messages")

    def __init__(
        self,
        bot: commands.Bot,
        generator: SpamDetectionGenerator = None,
        wipe_cache_delay: timedelta = timedelta(seconds=5),
    ):
        CacheBased.__init__(self, bot, wipe_cache_delay)
        EventManager.__init__(self)

        self.generator = (
            generator if generator is not None else DefaultSpamDetectionGenerator
        )
        self.punishments = []

        self.bot.add_listener(self.__handle_messages, "on_message")
        self.bot.add_listener(self.__handle_messages, "on_message_edit")

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
                    results.append(
                        SequenceMatcher(None, message, second_message).ratio()
                    )

        return sum(results) / len(results) if results else 0

    def add_punishments(self, punishments: List[Punishment]) -> None:
        self.punishments = punishments

    async def __handle_messages(self, message, edited_message=None):
        message = edited_message or message

        if not message.guild or message.author.bot:
            return

        member_last_messages = list(
            filter(lambda x: x.author == message.author, self.bot.cached_messages)
        )[-5:]

        if len(member_last_messages) <= 3 or not get_generator_response(
            self.generator, SpamDetectionGenerator, member_last_messages
        ):
            return

        # member_warnings are the number of times the member has spammed.
        member_warnings = (
            self._cache.setdefault(message.guild.id, {}).get(message.author.id, 0) + 1
        )
        self._cache[message.guild.id][message.author.id] = member_warnings

        await self.call_event("on_message_spam", member_last_messages, member_warnings)

        if punishment := get_relevant_punishment(self.punishments, member_warnings):
            await punishment.punishment_manager.punish(
                message, message.author, punishment
            )
