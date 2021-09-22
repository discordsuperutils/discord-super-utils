from typing import List

import discord
from discord.ext import commands

import discordSuperUtils


class MySpamDetector(discordSuperUtils.SpamDetectionGenerator):
    def generate(self, last_messages: List[discord.Message]) -> bool:
        # This is only an example, you can use the default generator if you want to.
        # The default generator ignores members with the 'ADMINISTRATOR' permission, and it triggers when it detects
        # similarity in the last 10 messages of the member.
        # You could also make this ignore roles, permissions, etc...

        return "Hey detector, i am spamming!" in last_messages[-1].content
        # Obviously, this isn't a good spam detection method.
        # I recommend using the default one which compares the similarity between the last 5 messages.
        # But of course, if you have a better idea to detect spam, you can make your custom spam detector.


bot = commands.Bot(command_prefix="-")
KickManager = discordSuperUtils.KickManager(bot)
AntiSpam = discordSuperUtils.SpamManager(bot)
# Incase you want to use the default spam detector, don't pass a spam detector.
AntiSpam.add_punishments([discordSuperUtils.Punishment(KickManager, punish_after=3)])


@AntiSpam.event()
async def on_message_spam(last_messages, member_warnings):
    # Member warnings represents the amount of times he has been detected for spam.
    print(f"{last_messages[0].author} is spamming! ({member_warnings}/3)")


@bot.event
async def on_ready():
    print("Anti spam is ready.", bot.user)


bot.run("token")
