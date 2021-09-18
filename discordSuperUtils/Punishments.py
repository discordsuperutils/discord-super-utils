from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    import discord
    from discord.ext import commands


class Punishment:
    """
    A punishment class that is used for punishing members.
    """

    def __init__(
        self,
        punishment_manager,
        punish_after: int = 3,
        punishment_reason: str = "No reason specified.",
        punishment_time: timedelta = timedelta(days=1),
    ):
        self.punishment_manager = punishment_manager
        self.punish_after = punish_after
        self.punishment_reason = punishment_reason
        self.punishment_time = punishment_time

        if not issubclass(type(punishment_manager), Punisher):
            raise TypeError(
                f"Manager of type '{type(punishment_manager)} is not supported.'"
            )


def get_relevant_punishment(
    punishments: List[Punishment], punish_count: int
) -> Optional[Punishment]:
    """
    Returns the punishment that is suitable for the punish count.

    :param punishments: The punishments to pick from.
    :type punishments: List[Punishment]
    :param punish_count: The punishment count.
    :type punish_count: int
    :rtype: Optional[Punishment]
    :return: The suitable punishment.
    """

    return {x.punish_after: x for x in punishments}.get(punish_count)


class Punisher(ABC):
    @abstractmethod
    async def punish(
        self, ctx: commands.Context, member: discord.Member, punishment: Punishment
    ) -> None:
        """
        The manager's punish function.

        :param ctx: The context of the punishments.
        :type ctx: commands.Context
        :param member: The member to punish.
        :type member: discord.Member
        :param punishment: The punishment to punish the member with.
        :type punishment: Punishment
        :rtype: None
        :return: None
        """
