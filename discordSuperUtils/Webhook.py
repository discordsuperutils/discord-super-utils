import discord
import aiohttp
import requests


class AsyncWebhook:
    def __init__(self, webhook: str):
        self.webhook = webhook

    @staticmethod
    async def to_json(embed: discord.Embed):
        return embed.to_dict()

    @classmethod
    async def pick_val(cls, embed, embeds):
        if not embed:
            return [(await cls.to_json(embd)) for embd in embeds]
        return [await cls.to_json(embed)]

    @classmethod
    async def list_to_json(cls, embeds: list):
        return [(await cls.to_json(embd)) for embd in embeds]

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
            "embeds": [self.to_json(embed)]
        }
        async with aiohttp.ClientSession() as session:
            return await session.post(self.webhook, json=data)

    async def send_embeds(self, embeds: list):
        data = {
            "content": "",
            "embeds": self.list_to_json(embeds)
        }
        async with aiohttp.ClientSession() as session:
            return await session.post(self.webhook, json=data)

    async def send_raw(self, data: dict):
        async with aiohttp.ClientSession() as session:
            return await session.post(self.webhook, json=data)


class Webhook:
    def __init__(self, webhook: str):
        self.webhook = webhook

    @staticmethod
    def to_json(embed: discord.Embed):
        return embed.to_dict()

    @classmethod
    def pick_val(cls, embed, embeds):
        if not embed:
            return [(cls.to_json(embd)) for embd in embeds]
        return [cls.to_json(embed)]

    @classmethod
    def list_to_json(cls, embeds: list):
        return [(cls.to_json(embd)) for embd in embeds]

    def send(self, text="", embed: discord.Embed = None, embeds: list = []):
        if embeds is None:
            embeds = []
        data = {
            "content": text,
            "embeds": self.pick_val(embed, embeds)
        }
        return requests.post(self.webhook, json=data)

    def send_embed(self, embed: discord.Embed):
        data = {
            "content": "",
            "embeds": [self.to_json(embed)]
        }
        return requests.post(self.webhook, json=data)

    def send_embeds(self, embeds: list):
        data = {
            "content": "",
            "embeds": self.list_to_json(embeds)
        }
        return requests.post(self.webhook, json=data)

    def send_raw(self, data: dict):
        return requests.post(self.webhook, json=data)

# it mostly works but I wanna add some stuff to it before releasing to pypi!
