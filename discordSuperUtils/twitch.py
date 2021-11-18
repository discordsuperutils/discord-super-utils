from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, List, Iterable

import aiohttp

from .base import DatabaseChecker

if TYPE_CHECKING:
    import discord
    from discord.ext import commands

__all__ = ("TwitchManager",)


class TwitchManager(DatabaseChecker):
    __slots__ = (
        "bot",
        "update_interval",
        "twitch_client_id",
        "twitch_client_secret",
        "session",
    )

    TWITCH_API_URL = "https://api.twitch.tv/helix"

    def __init__(
        self,
        bot: commands.Bot,
        twitch_client_id: str,
        twitch_client_secret: str,
        update_interval: int = 30,
    ) -> None:
        super().__init__(
            [
                {
                    "guild": "snowflake",
                    "channel": "string",
                }
            ],
            [
                "channels",
            ],
        )
        self.bot = bot

        self.twitch_client_id = twitch_client_id
        self.twitch_client_secret = twitch_client_secret

        self.update_interval = update_interval

        self._channel_cache: List[dict] = []
        self.session = None

        self.add_event(self._on_database_connect, "on_database_connect")

    async def _initialize(self) -> None:
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def _on_database_connect(self):
        self.bot.loop.create_task(self.__detect_streams())

    async def get_channel_status(self, channels: Iterable[str]) -> dict:
        await self._initialize()

        url = (
            self.TWITCH_API_URL + f"/streams?user_login={'&user_login='.join(channels)}"
        )

        r = await self.session.get(
            url,
            headers={
                "Client-ID": self.twitch_client_id,
                "Authorization": f"Bearer {self.twitch_client_secret}",
            },
        )

        r_json = await r.json()
        if "data" in r_json:
            for stream in r_json["data"]:
                stream["started_at"] = datetime.fromisoformat(stream["started_at"][:-1])

            return r_json["data"]

        return r_json

    async def add_channel(self, guild: discord.Guild, channel: str) -> None:
        await self.database.insertifnotexists(
            self.tables["channels"],
            {"guild": guild.id, "channel": channel},
            {"guild": guild.id, "channel": channel},
        )

    async def remove_channel(self, guild: discord.Guild, channel: str) -> None:
        await self.database.delete(
            self.tables["channels"], {"guild": guild.id, "channel": channel}
        )

    async def get_guild_channels(self, guild: discord.Guild) -> List[str]:
        channel_records = await self.database.select(
            self.tables["channels"], ["channel"], {"guild": guild.id}, True
        )

        return [record["channel"] for record in channel_records]

    @staticmethod
    def get_matching_channels(streams: List[dict], names: List[str]) -> List[dict]:
        return [
            stream
            for stream in streams
            if stream["user_name"].casefold() in [x.casefold() for x in names]
        ]

    @staticmethod
    def remove_channel_ids(streams: List[dict], channel_ids: List[int]) -> List[dict]:
        return [stream for stream in streams if stream["id"] not in channel_ids]

    async def __detect_streams(self) -> None:
        await self.bot.wait_until_ready()

        start_time = datetime.utcnow()

        while not self.bot.is_closed():
            guild_channels = {
                x: await self.get_guild_channels(x) for x in self.bot.guilds
            }
            twitch_channels = {
                channel for channels in guild_channels.values() for channel in channels
            }

            statuses = [
                status for status in await self.get_channel_status(twitch_channels)
            ]

            started_streams = self.remove_channel_ids(
                [status for status in statuses if start_time <= status["started_at"]],
                [x["id"] for x in self._channel_cache],
            )
            ended_streams = self.remove_channel_ids(
                self._channel_cache, [x["id"] for x in statuses]
            )

            for guild, channel_list in guild_channels.items():
                guild_started_streams = self.get_matching_channels(
                    started_streams, channel_list
                )
                guild_ended_streams = self.get_matching_channels(
                    ended_streams, channel_list
                )

                if guild_started_streams:
                    await self.call_event("on_stream", guild, guild_started_streams)
                if guild_ended_streams:
                    await self.call_event("on_stream_end", guild, guild_ended_streams)

            self._channel_cache = statuses

            await asyncio.sleep(self.update_interval)
