from __future__ import annotations

import asyncio
import aiohttp
import json
import discord
from typing import (
    TYPE_CHECKING,
    Union,
    Optional
)


class http:
    def __init__(self):
        """Pass"""

    async def send(self, url, data):
        async with aiohttp.ClientSession() as session:
            await session.post(url, json=data)

    async def add_global_slash_command(self, data, headers, applicationid):
        url = f"https://discord.com/api/v8/applications/{applicationid}/commands"
        async with aiohttp.ClientSession() as session:
            return await session.post(url, headers=headers, json=data)

