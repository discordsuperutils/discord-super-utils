import aiosqlite

import discordSuperUtils
from discord.ext import commands
import discord
import time
from datetime import datetime


bot = commands.Bot(command_prefix="-")
InfractionManager = discordSuperUtils.InfractionManager(bot)


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(await aiosqlite.connect('main.sqlite'))
    await InfractionManager.connect_to_database(database, "infractions")
    print('Infraction manager is ready.', bot.user)


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
    infraction = await InfractionManager.warn(member, reason)

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
    from_timestamp = time.time() - from_time

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
    from_timestamp = time.time() - from_time

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
