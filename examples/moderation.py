from datetime import datetime

import discord
from discord.ext import commands

import discordSuperUtils

bot = commands.Bot(command_prefix="-", intents=discord.Intents.all())

InfractionManager = discordSuperUtils.InfractionManager(bot)
BanManager = discordSuperUtils.BanManager(bot)
KickManager = discordSuperUtils.KickManager(bot)
MuteManager = discordSuperUtils.MuteManager(bot)

InfractionManager.add_punishments([
    discordSuperUtils.Punishment(KickManager, punish_after=3),
    discordSuperUtils.Punishment(MuteManager, punish_after=4),
    discordSuperUtils.Punishment(BanManager, punish_after=5)
])


@MuteManager.event()
async def on_unmute(member, reason):
    print(f"{member} has been unmuted. Mute reason: {reason}")


@BanManager.event()
async def on_unban(member, reason):
    print(f"{member} has been unbanned. ban reason: {reason}")


@BanManager.event()
async def on_punishment(ctx, member, punishment):
    await ctx.send(f"{member.mention} has been punished!")


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(...)
    await InfractionManager.connect_to_database(database, ["infractions"])
    await BanManager.connect_to_database(database, ["bans"])
    await MuteManager.connect_to_database(database, ["mutes"])

    print('Infraction manager is ready.', bot.user)


@bot.command()
async def mute(ctx,
               member: discord.Member,
               time_of_mute: discordSuperUtils.TimeConvertor,
               reason: str = "No reason specified."):
    try:
        await MuteManager.mute(member, reason, time_of_mute)
    except discordSuperUtils.AlreadyMuted:
        await ctx.send(f"{member} is already muted.")
    else:
        await ctx.send(f"{member} has been muted. Reason: {reason}")


@bot.command()
async def unmute(ctx, member: discord.Member):
    if await MuteManager.unmute(member):
        await ctx.send(f"{member.mention} has been unmuted.")
    else:
        await ctx.send(f"{member.mention} is not muted!")


@bot.command()
async def ban(ctx,
              member: discord.Member,
              time_of_ban: discordSuperUtils.TimeConvertor,
              reason: str = "No reason specified."):
    await ctx.send(f"{member} has been banned. Reason: {reason}")
    await BanManager.ban(member, reason, time_of_ban)


@bot.command()
async def unban(ctx, user: discord.User):
    if await BanManager.unban(user, guild=ctx.guild):
        await ctx.send(f"{user} has been unbanned.")
    else:
        await ctx.send(f"{user} is not banned.")


@bot.group(invoke_without_command=True)
async def infractions(ctx, member: discord.Member):
    member_infractions = await InfractionManager.get_infractions(member)

    await discordSuperUtils.PageManager(ctx, discordSuperUtils.generate_embeds(
        [f"**Reason: **{await infraction.reason()}\n"
         f"**ID: **{infraction.infraction_id}\n"
         f"**Date of Infraction: **{await infraction.datetime()}" for infraction in member_infractions],
        title=f"Infractions of {member}",
        fields=25,
        description=f"List of {member.mention}'s infractions."
    )).run()


@infractions.command()
async def add(ctx, member: discord.Member, reason: str = "No reason specified."):
    infraction = await InfractionManager.warn(ctx, member, reason)

    embed = discord.Embed(
        title=f"{member} has been warned.",
        color=0x00ff00
    )

    embed.add_field(name="Reason", value=await infraction.reason(), inline=False)
    embed.add_field(name="Infraction ID", value=infraction.infraction_id, inline=False)
    embed.add_field(name="Date of Infraction", value=str(await infraction.datetime()), inline=False)
    # Incase you don't like the Date of Infraction format you can change it using datetime.strftime

    await ctx.send(embed=embed)


@infractions.command()
async def get(ctx, member: discord.Member, infraction_id: str):
    infractions_found = await InfractionManager.get_infractions(member, infraction_id=infraction_id)

    if not infractions_found:
        await ctx.send(f"Cannot find infraction with id {infraction_id} on {member.mention}'s account")
        return

    infraction = infractions_found[0]

    embed = discord.Embed(
        title=f"Infraction found on {member}'s account!",
        color=0x00ff00
    )

    embed.add_field(name="Reason", value=await infraction.reason(), inline=False)
    embed.add_field(name="Infraction ID", value=infraction.infraction_id, inline=False)
    embed.add_field(name="Date of Infraction", value=str(await infraction.datetime()), inline=False)
    # Incase you don't like the Date of Infraction format you can change it using datetime.strftime

    await ctx.send(embed=embed)


@infractions.command()
async def get_before(ctx, member: discord.Member, from_time: discordSuperUtils.TimeConvertor):
    from_timestamp = datetime.utcnow().timestamp() - from_time

    member_infractions = await InfractionManager.get_infractions(member, from_timestamp=from_timestamp)

    await discordSuperUtils.PageManager(ctx, discordSuperUtils.generate_embeds(
        [f"**Reason: **{await infraction.reason()}\n"
         f"**ID: **{infraction.infraction_id}\n"
         f"**Date of Infraction: **{await infraction.datetime()}" for infraction in member_infractions],
        title=f"Infractions of {member}",
        fields=25,
        description=f"Shows a list of {member.mention}'s infractions before {datetime.fromtimestamp(from_timestamp)}."
    )).run()


@infractions.command()
async def clear(ctx, member: discord.Member):
    removed_infractions = []

    for infraction in await InfractionManager.get_infractions(member):
        removed_infractions.append(await infraction.delete())

    await discordSuperUtils.PageManager(ctx, discordSuperUtils.generate_embeds(
        [f"**Reason: **{infraction.reason}\n"
         f"**ID: **{infraction.infraction_id}\n"
         f"**Date of Infraction: **{infraction.date_of_infraction}" for infraction in removed_infractions],
        title=f"Removed Infractions",
        fields=25,
        description=f"List of infractions that were removed from {member.mention}."
    )).run()


@infractions.command()
async def remove(ctx, member: discord.Member, infraction_id: str):
    infractions_found = await InfractionManager.get_infractions(member, infraction_id=infraction_id)

    if not infractions_found:
        await ctx.send(f"Cannot find infraction with id {infraction_id} on {member.mention}'s account")
        return

    removed_infraction = await infractions_found[0].delete()

    embed = discord.Embed(
        title=f"Infraction removed from {member}'s account!",
        color=0x00ff00
    )

    embed.add_field(name="Reason", value=removed_infraction.reason, inline=False)
    embed.add_field(name="Infraction ID", value=removed_infraction.infraction_id, inline=False)
    embed.add_field(name="Date of Infraction", value=str(removed_infraction.date_of_infraction), inline=False)

    await ctx.send(embed=embed)


@infractions.command()
async def remove_before(ctx, member: discord.Member, from_time: discordSuperUtils.TimeConvertor):
    from_timestamp = datetime.utcnow().timestamp() - from_time

    member_infractions = await InfractionManager.get_infractions(member, from_timestamp=from_timestamp)
    removed_infractions = []

    for infraction in member_infractions:
        removed_infractions.append(await infraction.delete())

    await discordSuperUtils.PageManager(ctx, discordSuperUtils.generate_embeds(
        [f"**Reason: **{infraction.reason}\n"
         f"**ID: **{infraction.infraction_id}\n"
         f"**Date of Infraction: **{infraction.date_of_infraction}" for infraction in removed_infractions],
        title=f"Infractions of {member}",
        fields=25,
        description=f"Shows a list of {member.mention}'s removed infractions before {datetime.fromtimestamp(from_timestamp)}."
    )).run()


bot.run("token")
