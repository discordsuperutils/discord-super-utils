from .base import DatabaseChecker
from discord.ext import commands


class ApplicationManager(DatabaseChecker):
    def __init__(self, bot: commands.Bot):
        # super().__init__(
        #     [
        #         {
        #             "guild": "snowflake",
        #             "member": "snowflake",
        #             ""
        #         }
        #     ],
        #     ["applications_questions"]
        # )
        pass
