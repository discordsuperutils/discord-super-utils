from .base import DatabaseChecker
from .paginator import EmojiError


class ReactionManager(DatabaseChecker):
    def __init__(self, bot):
        super().__init__(
            [
                {
                    "guild": "snowflake",
                    "message": "snowflake",
                    "role": "snowflake",
                    "emoji": "string",
                    "remove_on_reaction": "smallnumber",
                }
            ],
            ["reaction_roles"],
        )

        self.bot = bot
        self.add_event(self.on_database_connect)

    async def on_database_connect(self):
        self.bot.add_listener(self.__handle_reactions, "on_raw_reaction_add")
        self.bot.add_listener(self.__handle_reactions, "on_raw_reaction_remove")

    @staticmethod
    def get_emoji_sql(emoji):
        if not emoji.is_custom_emoji():
            return str(emoji)

        emoji_string = f"<:{emoji.name}:{emoji.id}>"
        if emoji.animated:
            emoji_string = emoji_string[:1] + "a" + emoji_string[1:]

        return emoji_string

    async def __handle_reactions(self, payload):
        self._check_database()

        if payload.user_id == self.bot.user.id:
            return

        database_checks = {
            "guild": payload.guild_id,
            "message": payload.message_id,
            "emoji": self.get_emoji_sql(payload.emoji),
        }

        reaction_role_data = await self.database.select(
            self.tables["reaction_roles"], [], database_checks
        )

        if not reaction_role_data:
            return

        guild = self.bot.get_guild(payload.guild_id)
        role = guild.get_role(reaction_role_data["role"])
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        emoji = self.get_emoji_sql(payload.emoji)

        if emoji == reaction_role_data["emoji"]:
            member = (
                payload.member if payload.member else guild.get_member(payload.user_id)
            )

            if role is None:
                await self.call_event(
                    "on_reaction_event", guild, channel, message, member, emoji
                )

            else:
                if role not in member.roles:
                    await member.add_roles(role)
                elif reaction_role_data["remove_on_reaction"] == 1:
                    await member.remove_roles(role)

    @DatabaseChecker.uses_database
    async def create_reaction(
        self, guild, message, role, emoji, remove_on_reaction: int
    ):
        await self.database.insertifnotexists(
            self.tables["reaction_roles"],
            dict(
                zip(
                    self.tables_column_data[0],
                    [
                        guild.id,
                        message.id,
                        role.id if role is not None else role,
                        emoji,
                        int(remove_on_reaction),
                    ],
                )
            ),
            {"guild": guild.id, "message": message.id, "emoji": emoji},
        )

        if len(emoji) > 1:
            emoji = self.bot.get_emoji(emoji)

        try:
            await message.add_reaction(emoji)
        except Exception:
            raise EmojiError("Cannot add reaction to message.")

    async def delete_reaction(self, guild, message, emoji):
        await self.database.delete(
            self.tables["reaction_roles"],
            {"guild": guild.id, "message": message.id, "emoji": emoji},
        )

    async def get_reactions(self, guild=None):
        return await self.database.select(
            self.tables["reaction_roles"],
            [],
            {"guild": guild.id} if guild else {},
            True,
        )
