import discord


class BanManager:
    def __init__(self, bot):
        self.bot = bot
        self.bans = []
        self._tempbans = []