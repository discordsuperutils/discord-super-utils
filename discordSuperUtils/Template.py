from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import (
    List,
    Dict,
    Any,
    TYPE_CHECKING, Optional
)

import discord
from discord.guild import VerificationLevel

from .Base import DatabaseChecker

if TYPE_CHECKING:
    from discord.ext import commands
    from .Database import Database

__all__ = (
    "DictionaryConvertible",
    "TemplateInfo",
    "TemplateRole",
    "TemplateCategory",
    "TemplateTextChannel",
    "TemplateVoiceChannel",
    "Template",
    "TemplateManager"
)


class DictionaryConvertible(ABC):
    __slots__ = ()

    @classmethod
    @abstractmethod
    def from_dict(cls, convert_from: Dict[str, Any]) -> DictionaryConvertible:
        pass


class TemplateInfo(DictionaryConvertible):
    __slots__ = ("template_id", "guild", "afk_timeout", "mfa_level", "verification_level", "explict_content_filter")

    def __init__(self,
                 template_id: str,
                 guild: int,
                 afk_timeout: int,
                 mfa_level: int,
                 verification_level: VerificationLevel,
                 explict_content_filter: int):
        self.template_id = template_id
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
        convert_from["explict_content_filter"] = discord.ContentFilter(convert_from["explict_content_filter"] or 0)

        return cls(*list(convert_from.values()))


class TemplateCategory(DictionaryConvertible):
    __slots__ = ("name", "position", "category_id", "overwrites")

    def __init__(self, name: str, position: int, category_id: int, overwrites: Dict[int, int]):
        self.name = name
        self.position = position
        self.category_id = category_id
        self.overwrites = overwrites

    def __repr__(self):
        return f"<TemplateCategory id={self.category_id} name={self.name!r} position={self.position}>"

    def __str__(self):
        return f"<TemplateCategory name={self.name!r}>"

    @classmethod
    def from_dict(cls, convert_from: Dict[Any, Any]) -> TemplateCategory:
        return cls(*list(convert_from.values())[1:])


class TemplateTextChannel(DictionaryConvertible):
    __slots__ = ("name", "position", "category", "topic", "slowmode", "nsfw", "channel_id", "overwrites")

    def __init__(self,
                 name: str,
                 position: int,
                 category: int,
                 topic: str,
                 slowmode: int,
                 nsfw: bool,
                 channel_id: int,
                 overwrites: Dict[int, int]):
        self.name = name
        self.position = position
        self.category = category
        self.topic = topic
        self.slowmode = slowmode
        self.nsfw = nsfw
        self.channel_id = channel_id
        self.overwrites = overwrites

    def __repr__(self):
        return f"<TemplateTextChannel topic={self.topic} name={self.name!r} position={self.position}>"

    def __str__(self):
        return f"<TemplateTextChannel name={self.name!r}>"

    @classmethod
    def from_dict(cls, convert_from: Dict[str, Any]) -> TemplateTextChannel:
        convert_from["nsfw"] = bool(convert_from["nsfw"])
        print(convert_from)

        return cls(*list(convert_from.values())[1:])


class TemplateVoiceChannel(DictionaryConvertible):
    __slots__ = ("name", "position", "category", "bitrate", "user_limit", "channel_id", "overwrites")

    def __init__(self,
                 name: str,
                 position: int,
                 category: int,
                 bitrate: int,
                 user_limit: int,
                 channel_id: int,
                 overwrites: Dict[int, int]):
        self.name = name
        self.position = position
        self.category = category
        self.bitrate = bitrate
        self.user_limit = user_limit
        self.channel_id = channel_id
        self.overwrites = overwrites

    def __repr__(self):
        return f"<TemplateVoiceChannel limit={self.user_limit} name={self.name!r} position={self.position}>"

    def __str__(self):
        return f"<TemplateVoiceChannel name={self.name!r}>"

    @classmethod
    def from_dict(cls, convert_from: Dict[str, Any]) -> TemplateVoiceChannel:
        return cls(*list(convert_from.values())[1:])


class TemplateRole(DictionaryConvertible):
    __slots__ = ("default_role", "name", "color", "hoist", "position", "mentionable", "role_id", "permissions")

    def __init__(self,
                 default_role: bool,
                 name: str,
                 color: int,
                 hoist: bool,
                 position: int,
                 mentionable: bool,
                 role_id: int,
                 permissions: discord.Permissions):
        self.default_role = default_role
        self.name = name
        self.color = color
        self.hoist = hoist
        self.position = position
        self.mentionable = mentionable
        self.role_id = role_id
        self.permissions = discord.Permissions(permissions)

    def get_raw(self):
        return {
            "name": self.name,
            "hoist": self.hoist,
            "mentionable": self.mentionable,
            "color": self.color,
            "permissions": self.permissions
        }

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
    __slots__ = ("info", "categories", "text_channels", "voice_channels", "roles")

    def __init__(self,
                 info: TemplateInfo,
                 categories: List[TemplateCategory],
                 text_channels: List[TemplateTextChannel],
                 voice_channels: List[TemplateVoiceChannel],
                 roles: List[TemplateRole]):
        self.info = info
        self.categories = categories
        self.text_channels = text_channels
        self.voice_channels = voice_channels
        self.roles = roles

    def __repr__(self):
        return f"<Template template={self.info} categories={self.categories} text_channels={self.text_channels}>"

    def __str__(self):
        return f"Template template={self.info}"

    async def apply_settings(self, guild: discord.Guild, reason: str) -> None:
        await guild.edit(
            afk_timeout=self.info.afk_timeout,
            verification_level=self.info.verification_level,
            explicit_content_filter=self.info.explict_content_filter,
            reason=reason
        )

    async def apply_roles(self, guild: discord.Guild, reason: str) -> Dict[int, discord.Role]:
        roles = await asyncio.gather(
            *[
                await guild.default_role.edit(permissions=role.permissions, reason=reason)
                if role.default_role else
                await guild.create_role(**role.get_raw())
                for role in reversed(self.roles)
            ]
        )

        return dict(zip((x.role_id for x in reversed(self.roles)),
                        (role if role else guild.default_role for role in roles)))

    async def apply_categories(self, guild: discord.Guild, reason: str) -> Dict[int, discord.CategoryChannel]:
        categories = await asyncio.gather(
            *[
                await guild.create_category_channel(name=category.name, reason=reason)
                for category in self.categories
            ]
        )

        return dict(zip((category.category_id for category in self.categories), categories))

    async def apply_channels(self,
                             guild: discord.Guild,
                             reason: str,
                             categories: Dict[int, discord.CategoryChannel]) -> None:
        await asyncio.gather(*[await guild.create_text_channel(
            name=channel.name,
            position=channel.position,
            slowmode_delay=channel.slowmode,
            topic=channel.topic,
            nsfw=channel.nsfw,
            category=categories.get(channel.category),
            reason=reason) for channel in self.text_channels])

    async def apply_voice_channels(self,
                                   guild: discord.Guild,
                                   reason: str,
                                   categories: Dict[int, discord.CategoryChannel]) -> None:
        await asyncio.gather(*[await guild.create_voice_channel(
            name=channel.name,
            position=channel.position,
            category=categories.get(channel.category),
            bitrate=channel.bitrate,
            user_limit=channel.user_limit,
            reason=reason) for channel in self.voice_channels])

    async def apply(self, guild: discord.Guild) -> None:
        roles_to_delete = list(filter(
            lambda r: not r.managed and guild.default_role != r and guild.me.top_role.position > r.position,
            guild.roles
        ))

        reason = f"Applying template {self.info.template_id}"

        await asyncio.gather(*[role.delete(reason=reason) for role in roles_to_delete])
        await asyncio.gather(*[channel.delete(reason=reason) for channel in guild.channels])

        await self.apply_settings(guild, reason)
        await self.apply_roles(guild, reason)
        categories = await self.apply_categories(guild, reason)
        await self.apply_channels(guild, reason, categories)
        await self.apply_voice_channels(guild, reason, categories)

    @staticmethod
    def get_overwrite(overwrites: List[Dict[str, Any]], overwrite_object: int) -> Dict[int, int]:
        result_overwrites = {}

        for overwrite in overwrites:
            if overwrite["overwrite_object"] == overwrite_object:
                result_overwrites[overwrite["overwrite_key"]] = overwrite["overwrite_value"]

        return result_overwrites

    @classmethod
    async def get_template(cls, database: Database, tables: Dict[str, str], template_id: str) -> Template:
        checks = {'id': template_id}

        raw_categories = await database.select(tables["categories"], [], checks, fetchall=True)
        raw_text_channels = await database.select(tables["text_channels"], [], checks, fetchall=True)
        raw_voice_channels = await database.select(tables["voice_channels"], [], checks, fetchall=True)
        raw_roles = await database.select(tables["roles"], [], checks, fetchall=True)
        overwrites = await database.select(tables["overwrites"], [], checks, fetchall=True)

        return cls(
            TemplateInfo.from_dict(await database.select(tables["templates"], [], checks)),
            [TemplateCategory.from_dict(dict(x, **{"overwrites": cls.get_overwrite(overwrites, x["category_id"])}))
             for x in raw_categories],
            [TemplateTextChannel.from_dict(dict(x, **{"overwrites": cls.get_overwrite(overwrites, x["channel_id"])}))
             for x in raw_text_channels],
            [TemplateVoiceChannel.from_dict(dict(x, **{"overwrites": cls.get_overwrite(overwrites, x["channel_id"])}))
             for x in raw_voice_channels],
            [TemplateRole.from_dict(x) for x in raw_roles]
        )


class TemplateManager(DatabaseChecker):
    __slots__ = ("bot",)

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
                    "nsfw": "smallnumber",
                    "channel_id": "snowflake"
                },
                {
                    'id': "string",
                    "name": "string",
                    "position": "number",
                    "category": "snowflake",
                    "bitrate": "smallnumber",
                    "user_limit": "smallnumber",
                    "channel_id": "snowflake"
                },
                {
                    "id": "string",
                    "default_role": "smallnumber",
                    "name": "string",
                    "color": "number",
                    "hoist": "smallnumber",
                    "position": "number",
                    "mentionable": "smallnumber",
                    "role_id": "snowflake",
                    "permissions": "number"
                },
                {
                    "id": "string",
                    "overwrite_object": "snowflake",
                    "overwrite_key": "snowflake",
                    "overwrite_value": "number"
                }
            ],
            ['templates', 'categories', 'text_channels', 'voice_channels', 'roles', 'overwrites']
        )
        self.bot = bot

    async def get_template(self, template_id: str) -> Optional[Template]:
        return await Template.get_template(self.database, self.tables, template_id)

    async def write_overwrites(self,
                               template_id: str,
                               overwrites_object: int,
                               overwrites: discord.PermissionOverwrite) -> None:
        for x, y in overwrites.items():
            value = [pair.value for pair in y.pair() if pair.value > 0][0]

            await self.database.insert(self.tables["overwrites"],
                                       {
                                           "id": template_id,
                                           "overwrite_object": overwrites_object,
                                           "overwrite_key": x.id,
                                           "overwrite_value": value
                                       })

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
            await self.write_overwrites(template_id, category.id, category.overwrites)
            await self.database.insert(self.tables["categories"],
                                       {
                                           "id": template_id,
                                           "name": category.name,
                                           "position": category.position,
                                           "category_id": category.id
                                       })

        for channel in guild.text_channels:
            await self.write_overwrites(template_id, channel.id, channel.overwrites)
            await self.database.insert(self.tables["text_channels"],
                                       {
                                           "id": template_id,
                                           "name": channel.name,
                                           "position": channel.position,
                                           "category": channel.category_id,
                                           "topic": channel.topic,
                                           "slowmode": channel.slowmode_delay,
                                           "nsfw": int(channel.is_nsfw()),
                                           "channel_id": channel.id
                                       })

        for voice_channel in guild.voice_channels:
            await self.write_overwrites(template_id, voice_channel.id, voice_channel.overwrites)
            await self.database.insert(self.tables["voice_channels"],
                                       {
                                           "id": template_id,
                                           "name": voice_channel.name,
                                           "position": voice_channel.position,
                                           "category": voice_channel.category_id,
                                           "bitrate": voice_channel.bitrate,
                                           "user_limit": voice_channel.user_limit,
                                           "channel_id": voice_channel.id
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
                                           "mentionable": int(role.mentionable),
                                           "role_id": role.id,
                                           "permissions": role.permissions.value
                                       })

        return await Template.get_template(self.database, self.tables, template_id)
