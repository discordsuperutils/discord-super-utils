from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import (
    List,
    Dict,
    Any,
    TYPE_CHECKING, Optional
)

from .Base import DatabaseChecker
from discord.guild import VerificationLevel

if TYPE_CHECKING:
    from discord.ext import commands
    import discord
    from .Database import Database


class DictionaryConvertible(ABC):
    @classmethod
    @abstractmethod
    def from_dict(cls, convert_from: Dict[str, Any]) -> DictionaryConvertible:
        pass


class TemplateInfo(DictionaryConvertible):
    def __init__(self,
                 guild: int,
                 afk_timeout: int,
                 mfa_level: int,
                 verification_level: VerificationLevel,
                 explict_content_filter: int):
        self.guild = guild
        self.afk_timeout = afk_timeout
        self.mfa_level = mfa_level
        self.verification_level = verification_level
        self.explict_content_filter = explict_content_filter

    def __repr__(self):
        return f"<TemplateInfo guild={self.guild} mfa_level={self.mfa_level}>"

    def __str__(self):
        return f"<TemplateInfo guild={self.guild}>"

    @classmethod
    def from_dict(cls, convert_from: Dict[str, Any]) -> TemplateInfo:
        convert_from["verification_level"] = VerificationLevel(convert_from["verification_level"] or 0)

        return cls(*list(convert_from.values())[1:])


class TemplateCategory(DictionaryConvertible):
    def __init__(self, name: str, position: int, category_id: int):
        self.name = name
        self.position = position
        self.category_id = category_id

    def __repr__(self):
        return f"<TemplateCategory id={self.category_id} name={self.name!r} position={self.position}>"

    def __str__(self):
        return f"<TemplateCategory name={self.name!r}>"

    @classmethod
    def from_dict(cls, convert_from: Dict[str, Any]) -> TemplateCategory:
        return cls(*list(convert_from.values())[1:])


class TemplateTextChannel(DictionaryConvertible):
    def __init__(self, name: str, position: int, category: int, topic: str, slowmode: int, nsfw: bool):
        self.name = name
        self.position = position
        self.category = category
        self.topic = topic
        self.slowmode = slowmode
        self.nsfw = nsfw

    def __repr__(self):
        return f"<TemplateTextChannel topic={self.topic} name={self.name!r} position={self.position}>"

    def __str__(self):
        return f"<TemplateTextChannel name={self.name!r}>"

    @classmethod
    def from_dict(cls, convert_from: Dict[str, Any]) -> TemplateTextChannel:
        convert_from["nsfw"] = bool(convert_from["nsfw"])

        return cls(*list(convert_from.values())[1:])


class TemplateVoiceChannel(DictionaryConvertible):
    def __init__(self, name: str, position: int, category: int, bitrate: int, user_limit: int):
        self.name = name
        self.position = position
        self.category = category
        self.bitrate = bitrate
        self.user_limit = user_limit

    def __repr__(self):
        return f"<TemplateVoiceChannel limit={self.user_limit} name={self.name!r} position={self.position}>"

    def __str__(self):
        return f"<TemplateVoiceChannel name={self.name!r}>"

    @classmethod
    def from_dict(cls, convert_from: Dict[str, Any]) -> TemplateVoiceChannel:
        return cls(*list(convert_from.values())[1:])


class TemplateRole(DictionaryConvertible):
    def __init__(self, default_role: bool, name: str, color: int, hoist: bool, position: int, mentionable: bool):
        self.default_role = default_role
        self.name = name
        self.color = color
        self.hoist = hoist
        self.position = position
        self.mentionable = mentionable

    def __repr__(self):
        return f"<TemplateRole hoist={self.hoist} name={self.name!r} position={self.position} color={self.color}>"

    def __str__(self):
        return f"<TemplateRole name={self.name!r}>"

    @classmethod
    def from_dict(cls, convert_from: Dict[str, Any]) -> TemplateRole:
        convert_from["default_role"] = bool(convert_from["default_role"])
        convert_from["hoist"] = bool(convert_from["hoist"])
        convert_from["mentionable"] = bool(convert_from["mentionable"])

        return cls(*list(convert_from.values())[1:])


class Template:
    def __init__(self,
                 template: TemplateInfo,
                 categories: List[TemplateCategory],
                 text_channels: List[TemplateTextChannel],
                 voice_channels: List[TemplateVoiceChannel],
                 roles: List[TemplateRole]):
        self.template = template
        self.categories = categories
        self.text_channels = text_channels
        self.voice_channels = voice_channels
        self.roles = roles

    def __repr__(self):
        return f"<Template template={self.template} categories={self.categories} text_channels={self.text_channels}>"

    def __str__(self):
        return f"Template template={self.template}"

    @classmethod
    async def get_template(cls, database: Database, tables: Dict[str, str], template_id: str) -> Template:
        checks = {'id': template_id}

        raw_categories = await database.select(tables["categories"], [], checks, fetchall=True)
        raw_text_channels = await database.select(tables["text_channels"], [], checks, fetchall=True)
        raw_voice_channels = await database.select(tables["voice_channels"], [], checks, fetchall=True)
        raw_roles = await database.select(tables["roles"], [], checks, fetchall=True)

        return cls(
            TemplateInfo.from_dict(await database.select(tables["templates"], [], checks)),
            [TemplateCategory.from_dict(x) for x in raw_categories],
            [TemplateTextChannel.from_dict(x) for x in raw_text_channels],
            [TemplateVoiceChannel.from_dict(x) for x in raw_voice_channels],
            [TemplateRole.from_dict(x) for x in raw_roles]
        )


class TemplateManager(DatabaseChecker):
    def __init__(self, bot: commands.Bot):
        super().__init__(
            [
                {
                    'id': "string",
                    'guild': 'snowflake',
                    "afk_timeout": "number",
                    "mfa_level": "smallnumber",
                    "verification_level": "smallnumber",
                    "explict_content_filter": "smallnumber"
                },
                {
                    'id': "string",
                    "name": "string",
                    "position": "number",
                    "category_id": "snowflake"
                },
                {
                    'id': "string",
                    "name": "string",
                    "position": "number",
                    "category": "snowflake",
                    "topic": "string",
                    "slowmode": "number",
                    "nsfw": "smallnumber"
                },
                {
                    'id': "string",
                    "name": "string",
                    "position": "number",
                    "category": "snowflake",
                    "bitrate": "smallnumber",
                    "user_limit": "smallnumber"
                },
                {
                    "id": "string",
                    "default_role": "smallnumber",
                    "name": "string",
                    "color": "number",
                    "hoist": "smallnumber",
                    "position": "number",
                    "mentionable": "smallnumber"
                }
            ],
            ['templates', 'categories', 'text_channels', 'voice_channels', 'roles']
        )
        self.bot = bot

    async def get_template(self, template_id: str) -> Optional[Template]:
        return await Template.get_template(self.database, self.tables, template_id)

    async def create_template(self, guild: discord.Guild) -> Template:
        template_id = str(uuid.uuid4())

        await self.database.insert(self.tables["templates"],
                                   {
                                       'guild': guild.id,
                                       'id': template_id,
                                       'afk_timeout': guild.afk_timeout,
                                       'mfa_level': guild.mfa_level,
                                       'verification_level': guild.verification_level.value,
                                       'explict_content_filter': guild.explicit_content_filter.value
                                   })

        for category in guild.categories:
            await self.database.insert(self.tables["categories"],
                                       {
                                           "id": template_id,
                                           "name": category.name,
                                           "position": category.position,
                                           "category_id": category.id
                                       })

        for channel in guild.text_channels:
            await self.database.insert(self.tables["text_channels"],
                                       {
                                           "id": template_id,
                                           "name": channel.name,
                                           "position": channel.position,
                                           "category": channel.category_id,
                                           "topic": channel.topic,
                                           "slowmode": channel.slowmode_delay,
                                           "nsfw": int(channel.is_nsfw())
                                       })

        for voice_channel in guild.voice_channels:
            await self.database.insert(self.tables["voice_channels"],
                                       {
                                           "id": template_id,
                                           "name": voice_channel.name,
                                           "position": voice_channel.position,
                                           "category": voice_channel.category_id,
                                           "bitrate": voice_channel.bitrate,
                                           "user_limit": voice_channel.user_limit
                                       })

        for role in guild.roles:
            await self.database.insert(self.tables["roles"],
                                       {
                                           "id": template_id,
                                           "default_role": int(role.is_default()),
                                           "name": role.name,
                                           "color": role.color.value,
                                           "hoist": int(role.hoist),
                                           "position": role.position,
                                           "mentionable": int(role.mentionable)
                                       })

        return await Template.get_template(self.database, self.tables, template_id)
