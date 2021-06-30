from .Base import EventManager
from .Database import DatabaseManager
from .Paginator import EmojiError

reaction_keys = ['guild', 'message', 'role', 'emoji', 'remove_on_reaction']
reaction_types = ['INTEGER', 'INTEGER', 'INTEGER', 'TEXT', 'INTEGER']


class ReactionManager(EventManager):
    def __init__(self, database: DatabaseManager, table, bot):
        super().__init__()
        self.database = database
        self.table = table
        self.bot = bot

        self.__create_table(reaction_keys, reaction_types, self.table)
        self.bot.add_listener(self.__handle_reactions, "on_raw_reaction_add")
        self.bot.add_listener(self.__handle_reactions, "on_raw_reaction_remove")

    @classmethod
    def format_data(cls, data):
        formatted_data = {}
        for key, value in zip(reaction_keys, data):
            formatted_data[key] = value

        return formatted_data

    @classmethod
    def checks(cls, guild_id, message_id, emoji):
        return [
            {'guild': guild_id},
            {'message': message_id},
            {'emoji': emoji}
        ]

    def __create_table(self, names, types, table_name):
        columns = [{'name': x, 'type': y} for x, y in zip(names, types)]
        self.database.createtable(table_name, columns, True)

    async def __handle_reactions(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        database_checks = self.checks(payload.guild_id,
                                      payload.message_id,
                                      payload.emoji.id if payload.emoji.id is not None else str(payload.emoji))

        reaction_role_data = self.database.select(reaction_keys, self.table, database_checks)

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
        self.database.insertifnotexists(reaction_keys, [
            guild.id,
            message.id,
            role.id if role is not None else role,
            emoji,
            remove_on_reaction
        ], self.table, self.checks(guild.id, message.id, emoji))

        if len(emoji) > 1:
            emoji = self.bot.get_emoji(emoji)

        try:
            await message.add_reaction(emoji)
        except:
            raise EmojiError("Cannot add reaction to message.")

    async def delete_reaction(self, guild, message, emoji):
        self.database.delete(self.table, self.checks(guild.id, message.id, emoji))