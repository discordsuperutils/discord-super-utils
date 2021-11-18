from typing import List

import discord

from discord.ext import commands

import discordSuperUtils

bot = commands.Bot(command_prefix="-")
TwitchManager = discordSuperUtils.TwitchManager(bot, "CLIENT_ID", "CLIENT_SECRET")


def add_stream_fields(embed: discord.Embed, stream: dict):
    embed.add_field(
        name="Title",
        value=f"[{stream['title']}](https://twitch.tv/{stream['user_name']})",
        inline=False,
    )
    embed.add_field(name="Game", value=stream["game_name"], inline=False)
    embed.add_field(name="Viewers", value=str(stream["viewer_count"]), inline=False)
    embed.add_field(
        name="Started At", value=stream["started_at"], inline=False
    )  # You can format it.
    embed.add_field(
        name="Mature",
        value="Yes" if stream["is_mature"] else "No",
        inline=False,
    )
    embed.add_field(name="Language", value=stream["language"].upper(), inline=False)
    embed.set_image(url=stream["thumbnail_url"].format(height=248, width=440))


@TwitchManager.event()
async def on_stream(guild: discord.Guild, streams: List[dict]):
    channel = guild.get_channel(...)

    if channel:
        for stream in streams:
            embed = discord.Embed(
                title=f"{stream['user_name']} is now live!", color=0x00FF00
            )

            add_stream_fields(embed, stream)

            await channel.send(embed=embed)


@TwitchManager.event()
async def on_stream_end(guild: discord.Guild, streams: List[dict]):
    channel = guild.get_channel(...)

    if channel:
        for stream in streams:
            embed = discord.Embed(
                title=f"{stream['user_name']} has stopped streaming!", color=0x00FF00
            )

            add_stream_fields(embed, stream)

            await channel.send(embed=embed)


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(...)
    await TwitchManager.connect_to_database(
        database,
        ["channels"],
    )
    print("Twitch manager is ready.", bot.user)


@bot.command()
async def lookup(ctx, *, channel: str):
    status = await TwitchManager.get_channel_status([channel])
    stream_info = next(iter(status), None)

    if not stream_info:
        await ctx.send(f"'{channel}' is offline.")
        return

    embed = discord.Embed(title=f"'{channel}' is currently streaming!", color=0x00FF00)

    add_stream_fields(embed, stream_info)

    await ctx.send(embed=embed)


@bot.command()
async def add(ctx, *, channel: str):
    await TwitchManager.add_channel(ctx.guild, channel)
    await ctx.send(f"Added channel '{channel}'.")


@bot.command()
async def remove(ctx, *, channel: str):
    await TwitchManager.remove_channel(ctx.guild, channel)
    await ctx.send(f"Removed channel '{channel}'.")


bot.run("token")
