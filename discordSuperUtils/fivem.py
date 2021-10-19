from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import aiohttp
import aiohttp.client_exceptions


__all__ = ("ServerNotFound", "FiveMPlayer", "FiveMServer")


class ServerNotFound(Exception):
    """Raises an error when a server is invalid or offline."""


@dataclass
class FiveMPlayer:
    """
    Represents a FiveM player.
    """

    id: int
    identifiers: Dict[str, str]
    name: str
    ping: int

    @classmethod
    def from_dict(cls, player_dict: dict) -> FiveMPlayer:
        """
        Creates a FiveM player object from a dict.

        :param dict player_dict: The player information.
        :return: The FiveM player.
        :rtype: FiveMPlayer
        """

        identifiers = dict([x.split(":") for x in player_dict["identifiers"]])
        return cls(
            player_dict["id"], identifiers, player_dict["name"], player_dict["ping"]
        )


@dataclass
class FiveMServer:
    """
    Represents a FiveM server.
    """

    ip: str
    resources: List[str]
    players: List[FiveMPlayer]
    name: str
    variables: Dict[str, str]

    @classmethod
    async def fetch(cls, ip: str) -> Optional[FiveMServer]:
        """
        |coro|

        Fetches the server and returns the server object.
        The server object includes players, resources, name, variables

        :param ip: The server IP.
        :return: The FiveM server.
        :rtype: Optional[FiveMServer]
        """

        base_address = "http://" + ip + "/"

        async with aiohttp.ClientSession() as session:
            try:
                await session.get(base_address)  # Server status check
            except (
                aiohttp.client_exceptions.ClientConnectorError,
                aiohttp.client_exceptions.InvalidURL,
            ):
                raise ServerNotFound(f"Server '{ip}' is invalid or offline.")

            players_request = await session.get(base_address + "players.json")
            info_request = await session.get(base_address + "info.json")
            dynamic_info_request = await session.get(base_address + "dynamic.json")

            info = await info_request.json(content_type=None)
            players = await players_request.json(content_type=None)
            dynamic = await dynamic_info_request.json(content_type=None)
            # This is still included in the session because parsing the json outside of it sometimes doesnt work
            # and block the program (?) :(

        return cls(
            ip,
            info["resources"],
            [FiveMPlayer.from_dict(player) for player in players],
            dynamic["hostname"],
            info["vars"],
        )
