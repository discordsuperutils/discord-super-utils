import discord
from discord.ext import commands

import discordSuperUtils


class MyMessageGenerator(discordSuperUtils.MessageResponseGenerator):
    def generate(self, message: discord.Message) -> bool:
        # This is only an example, you can use the default generator if you want to.
        # The default generator ignores members with the 'ADMINISTRATOR' permission, and it triggers when it detects
        # a URL or a discord invite.
        # You could also make this ignore roles, permissions, etc...

        return "bad-word" in message.content


bot = commands.Bot(command_prefix="-")
KickManager = discordSuperUtils.KickManager(bot)
MessageFilter = discordSuperUtils.MessageFilter(
    bot, MyMessageGenerator(), delete_message=True
)
# Incase you want to use the default message generator, don't pass a message generator.
MessageFilter.add_punishments(
    [discordSuperUtils.Punishment(KickManager, punish_after=3)]
)


@MessageFilter.event()
async def on_inappropriate_message(message, member_warnings):
    # Member warnings represents the amount of inappropriate messages the message author sent.
    print(f"{message.author} sent an inappropriate message! ({member_warnings}/3)")


@bot.event
async def on_ready():
    print("Message filter is ready.", bot.user)


bot.run("token")
