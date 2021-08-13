from .Base import EventManager, generate_column_types
from .Paginator import EmojiError

database_keys = ['guild', 'message', 'role', 'emoji', 'remove_on_reaction']


class ReactionManager(EventManager):
    def __init__(self, database, table, bot):
        super().__init__()
        self.database = database
        self.table = table
        self.bot = bot

        self.__create_table()

        self.bot.add_listener(self.__handle_reactions, "on_raw_reaction_add")
        self.bot.add_listener(self.__handle_reactions, "on_raw_reaction_remove")

    def __create_table(self):
        types = generate_column_types(['snowflake', 'snowflake', 'snowflake', 'string', 'smallnumber'],
                                      type(self.database.database))
        columns = [{'name': x, 'type': y} for x, y in zip(database_keys, types)] if types else None
        self.database.create_table(self.table, columns, True)

    @classmethod
    def format_data(cls, data):
        return {key: value for key, value in zip(database_keys, data)}

    async def __handle_reactions(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        database_checks = {'guild': payload.guild_id,
                           'message': payload.message_id,
                           'emoji': payload.emoji.id if payload.emoji.id is not None else str(payload.emoji)}

        reaction_role_data = self.database.select(database_keys, self.table, database_checks)

        if not reaction_role_data:
            return

        formatted_data = self.format_data(reaction_role_data)

        guild = self.bot.get_guild(payload.guild_id)
        role = guild.get_role(formatted_data["role"])
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        emoji = str(payload.emoji) if payload.emoji.id is None else str(payload.emoji.id)

        if emoji == formatted_data["emoji"]:
            if role is None:
                await self.call_event('on_reaction_event', guild, channel, message, payload.member, emoji)

            else:
                if role not in payload.member.roles:
                    await payload.member.add_roles(role)
                elif formatted_data['remove_on_reaction'] == 1:
                    await payload.member.remove_roles(role)

    async def create_reaction(self, guild, message, role, emoji, remove_on_reaction):
        self.database.insertifnotexists(dict(zip(database_keys, [
            guild.id,
            message.id,
            role.id if role is not None else role,
            emoji,
            remove_on_reaction
        ])), self.table, {'guild': guild.id, 'message': message.id, 'emoji': emoji})

        if len(emoji) > 1:
            emoji = self.bot.get_emoji(emoji)

        try:
            await message.add_reaction(emoji)
        except Exception:
            raise EmojiError("Cannot add reaction to message.")

    def delete_reaction(self, guild, message, emoji):
        self.database.delete(self.table, {'guild': guild.id, 'message': message.id, 'emoji': emoji})

    def get_reactions(self, **kwargs):
        reactions = self.database.select(database_keys, self.table, kwargs, True)
        return [self.format_data(reaction) for reaction in reactions]
