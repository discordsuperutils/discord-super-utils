from typing import Optional, Union

from discord.ext import commands


def isfloat(string: str) -> bool:
    """
    This function receives a string and returns if it is a float or not.

    :param str string: The string to check.
    :return: A boolean representing if the string is a float.
    :rtype: bool
    """

    try:
        float(string)
        return True
    except (ValueError, TypeError):
        return False


class TimeConvertor(commands.Converter):
    """
    Converts a given argument to an int that represents time in seconds.

    Examples
    ----------
        7d: 604800 (7 days in seconds)

        1m: 60 (1 minute in seconds)

        heyh: BadArgument ('hey' is not an int)

        100j: BadArgument ('j' is not a valid time multiplier)
    """

    async def convert(
        self, ctx: commands.Context, argument: str
    ) -> Optional[Union[int, float]]:
        time_multipliers = {
            "s": 1,
            "m": 60,
            "h": 60 * 60,
            "d": 60 * 60 * 24,
            "w": 60 * 60 * 24 * 7,
        }

        permanent = ["permanent", "perm", "0"]
        if argument.lower() in permanent:
            return 0

        if not isfloat(argument[:-1]) or argument[-1] not in time_multipliers.keys():
            raise commands.BadArgument(
                f"Invalid time argument provided, cannot convert '{argument}' to time."
            )

        return float(argument[:-1]) * time_multipliers[argument[-1]]
