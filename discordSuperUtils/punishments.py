from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    import discord
    from discord.ext import commands


@dataclass
class Punishment:
    """
    A punishment class that is used for punishing members.
    """

    punishment_manager: Punisher
    punish_after: int = 3
    punishment_reason: str = "No reason specified."
    punishment_time: timedelta = timedelta(days=1)

    def __post_init__(self):
        if not issubclass(type(self.punishment_manager), Punisher):
            raise TypeError(
                f"Manager of type '{type(self.punishment_manager)} is not supported.'"
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
        |coro|

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
