from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, List, Iterable

import aiohttp

from .base import DatabaseChecker

if TYPE_CHECKING:
    import discord
    from discord.ext import commands

__all__ = ("TwitchManager", "TwitchAuthorizationError", "get_twitch_oauth_key")


async def get_twitch_oauth_key(client_id: str, client_secret: str) -> str:
    """
    Gets the Twitch OAuth key from the Twitch API.

    :param client_id: The client ID.
    :param client_secret: The client secret.
    :return: The OAuth key.
    """

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://id.twitch.tv/oauth2/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
        ) as resp:
            resp_json = await resp.json()
            return resp_json["access_token"]


class TwitchAuthorizationError(Exception):
    """
    Raises an error when the Twitch API returns an authorization error.
    """


class TwitchManager(DatabaseChecker):
    """
    Represents a twitch notification manager.
    """

    __slots__ = (
        "bot",
        "update_interval",
        "twitch_client_id",
        "twitch_access_token",
        "session",
        "authorization_headers",
    )

    TWITCH_API_URL = "https://api.twitch.tv/helix"

    def __init__(
        self,
        bot: commands.Bot,
        twitch_client_id: str,
        twitch_access_token: str,
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
        self.twitch_access_token = twitch_access_token

        self.authorization_headers = {
            "Client-ID": self.twitch_client_id,
            "Authorization": f"Bearer {self.twitch_access_token}",
        }

        self.update_interval = update_interval

        self._channel_cache: List[dict] = []
        self.session = None

        self.add_event(self._on_database_connect, "on_database_connect")

    async def _initialize(self) -> None:
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def _on_database_connect(self):
        self.bot.loop.create_task(self.__detect_streams())

    async def get_channel_status(self, channels: Iterable[str]) -> list:
        """
        |coro|

        Gets the live status of the given channels.

        :param Iterable[str] channels: The channels.
        :return: The live statuses of the channels or the error dictionary.
        :rtype: list
        :raises: TwitchAuthorizationError: If the Twitch API returns an authorization error.
        """

        await self._initialize()

        url = (
            self.TWITCH_API_URL + f"/streams?user_login={'&user_login='.join(channels)}"
        )

        r = await self.session.get(
            url,
            headers=self.authorization_headers,
        )

        r_json = await r.json()
        if "data" in r_json:
            for stream in r_json["data"]:
                stream["started_at"] = datetime.fromisoformat(stream["started_at"][:-1])

            return r_json["data"]

        raise TwitchAuthorizationError(r_json["message"])

    async def add_channel(self, guild: discord.Guild, channel: str) -> None:
        """
        |coro|

        Adds a channel to the guild list.

        :param discord.Guild guild: The guild.
        :param str channel: The channel.
        :return: None
        :rtype: None
        """

        await self.database.insertifnotexists(
            self.tables["channels"],
            {"guild": guild.id, "channel": channel},
            {"guild": guild.id, "channel": channel},
        )

    async def remove_channel(self, guild: discord.Guild, channel: str) -> None:
        """
        |coro|

        Removes a channel from the guild list.

        :param discord.Guild guild: The guild.
        :param str channel: The channel.
        :return: None
        :rtype: None
        """

        await self.database.delete(
            self.tables["channels"], {"guild": guild.id, "channel": channel}
        )

    async def get_guild_channels(self, guild: discord.Guild) -> List[str]:
        """
        |coro|

        Returns the channels of the guild.

        :param discord.Guild guild: The guild.
        :return: The channels.
        :rtype: List[str]
        """

        channel_records = await self.database.select(
            self.tables["channels"], ["channel"], {"guild": guild.id}, True
        )

        return [record["channel"] for record in channel_records]

    @staticmethod
    def get_matching_channels(streams: List[dict], names: List[str]) -> List[dict]:
        """
        Returns the streams that match the given names.

        :param List[dict] streams: The streams.
        :param List[str] names: The names.
        :return: The streams that match the given names.
        :rtype: List[dict]
        """

        return [
            stream
            for stream in streams
            if stream["user_name"].casefold() in [x.casefold() for x in names]
        ]

    @staticmethod
    def remove_channel_ids(streams: List[dict], channel_ids: List[int]) -> List[dict]:
        """
        Removes the channels that are in the given list that match the channel ids.

        :param List[dict] streams: The streams.
        :param List[int] channel_ids: The channel ids.
        :return: The result channels.
        :rtype: List[dict]
        """

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

            statuses = await self.get_channel_status(twitch_channels)

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
