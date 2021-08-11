import discord
import aiohttp
import requests

class AsyncWebhook:
    def __init__(self, webhook: str):
        self.webhook = webhook

    @staticmethod
    async def pick_val(embed, embeds):
        if not embed:
            return embeds
        return [embed]

    async def send(self, text="", embed: discord.Embed = None, embeds: list = []):
        if embeds is None:
            embeds = []
        data = {
            "content": text,
            "embeds": await self.pick_val(embed, embeds)
        }
        async with aiohttp.ClientSession() as session:
            return await session.post(self.webhook, json=data)

    async def send_embed(self, embed: discord.Embed):
        data = {
            "content": "",
            "embeds": [embed]
        }
        async with aiohttp.ClientSession() as session:
            return await session.post(self.webhook, json=data)

    async def send_embeds(self, embeds : list):
        data = {
            "content": "",
            "embeds": embeds
        }
        async with aiohttp.ClientSession() as session:
            return await session.post(self.webhook, json=data)

    async def send_raw(self, data: dict):
        async with aiohttp.ClientSession() as session:
            return await session.post(self.webhook, json=data)


class Webhook:
    def __int__(self, webhook : str):
        self.webhook = webhook

    @staticmethod
    def pick_val(embed, embeds):
        if not embed:
            return embeds
        return [embed]

    def send(self, text="", embed: discord.Embed = None, embeds: list = []):
        if embeds is None:
            embeds = []
        data = {
            "content": text,
            "embeds": await self.pick_val(embed, embeds)
        }
        return requests.post(self.webhook, json=data)

    def send_embed(self, embed: discord.Embed):
        data = {
            "content": "",
            "embeds": [embed]
        }
        return requests.post(self.webhook, json=data)

    def send_embeds(self, embeds: list):
        data = {
            "content": "",
            "embeds": embeds
        }
        return requests.post(self.webhook, json=data)

    def send_raw(self, data: dict):
        return requests.post(self.webhook, json=data)

    #not finished adam i am tired i will finih tmrw or sum