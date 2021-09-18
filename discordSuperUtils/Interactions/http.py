from __future__ import annotations

from typing import Dict, Any

import aiohttp


__all__ = ("HTTPClient",)


class HTTPClient:
    """
    Represents a HTTP client that handles interactions.
    """

    __slots__ = ("bot_token", "session")

    def __init__(self, bot_token: str, session: aiohttp.ClientSession = None):
        self.bot_token = bot_token
        self.session = session or aiohttp.ClientSession()

    async def request(
        self,
        request_type: str,
        url: str,
        payload: Dict[str, Any] = None,
        headers: Dict[str, Any] = None,
    ) -> str:
        """
        |coro|

        The website request method of the HTTP client.

        :param request_type: The request type.
        :type request_type: str
        :param url: The url.
        :type url: str
        :param payload: The payload.
        :type payload: Dict[str, Any]
        :param headers: The headers.
        :type headers: Dict[str, Any]
        :return: The response.
        :rtype: str
        """

        r = await self.session.request(
            request_type.upper(), url, json=payload or {}, headers=headers or {}
        )
        return await r.text()

    async def add_slash_command(
        self, payload: Dict[str, Any], application_id: int
    ) -> None:
        """
        |coro|

        The slash command creator method.

        :param payload: The payload of the creation.
        :type payload: Dict[str, Any]
        :param application_id: The application id of the bot (user id)
        :type application_id: int
        :rtype: None
        :return: None
        """

        url = f"https://discord.com/api/v9/applications/{application_id}/commands"
        headers = {
            "Authorization": self.bot_token,
        }

        await self.request("POST", url, payload, headers)
