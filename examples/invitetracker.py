import discord
from discord.ext import commands

import discordSuperUtils

bot = commands.Bot(command_prefix="-", intents=discord.Intents.all())
InviteTracker = discordSuperUtils.InviteTracker(bot)


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(...)
    await InviteTracker.connect_to_database(database, ["invites"])
    print('Invite tracker is ready.', bot.user)


@bot.event
async def on_member_join(member):
    invite = await InviteTracker.get_invite(member)
    inviter = await InviteTracker.fetch_inviter(invite)
    await InviteTracker.register_invite(invite, member, inviter)

    channel = bot.get_channel(...)
    await channel.send(
        f"{member.mention} was invited by {inviter.mention if inviter else None} with code {invite.code}")


@bot.command()
async def info(ctx, member: discord.Member = None):
    member = ctx.author if not member else member
    invited_members = await InviteTracker.get_user_info(member).get_invited_users()

    await ctx.send(f"{member.mention} invited the following members: " + ', '.join(str(x) for x in invited_members))
    # Now, instead of sending that message you can filter the invited members and sort it to your liking.
    # I recommend sorting it into alts, left, total, etc and then sending an embed containing that information.


bot.run("token")
