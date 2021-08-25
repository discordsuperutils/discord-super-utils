import aiosqlite
import discord

import discordSuperUtils
from discord.ext import commands


bot = commands.Bot(command_prefix='-')


class Leveling(commands.Cog, discordSuperUtils.CogManager.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.RoleManager = discordSuperUtils.RoleManager()
        self.LevelingManager = discordSuperUtils.LevelingManager(bot, self.RoleManager)
        super().__init__()  # Make sure you define your managers before running CogManager.Cog's __init__ function.
        # Incase you do not, CogManager.Cog wont find the managers and will not link them to the events.
        # Alternatively, you can pass your managers in CogManager.Cog's __init__ function incase you are using the same
        # managers in different files, I recommend saving the managers as attributes on the bot object, instead of
        # importing them.

    @commands.Cog.listener()
    async def on_ready(self):
        database = discordSuperUtils.DatabaseManager.connect(await aiosqlite.connect("main.sqlite"))
        await self.RoleManager.connect_to_database(database, "xp_roles")
        await self.LevelingManager.connect_to_database(database, "xp")

        print('Leveling manager is ready.', self.bot.user)

    @discordSuperUtils.CogManager.event(discordSuperUtils.LevelingManager)
    async def on_level_up(self, message, member_data, roles):
        await message.reply(f"You are now level {await member_data.level()}" + (f", you have received the {roles[0]}"
                                                                                f" role." if roles else ""))

    @commands.command()
    async def rank(self, ctx):
        member_data = await self.LevelingManager.get_account(ctx.author)

        if member_data:
            await ctx.send(
                f'You are currently level **{await member_data.level()}**, with **{await member_data.xp()}** XP.')
        else:
            await ctx.send(f"I am still creating your account! please wait a few seconds.")

    @commands.command()
    async def set_roles(self, ctx, *roles: discord.Role):
        await self.RoleManager.set_roles(ctx.guild, {"roles": roles})

    @commands.command()
    async def leaderboard(self, ctx):
        guild_leaderboard = await self.LevelingManager.get_leaderboard(ctx.guild)
        formatted_leaderboard = [f"Member: {x.member}, XP: {await x.xp()}" for x in guild_leaderboard]

        await discordSuperUtils.PageManager(ctx, discordSuperUtils.generate_embeds(
            formatted_leaderboard,
            title="Leveling Leaderboard",
            fields=25,
            description=f"Leaderboard of {ctx.guild}"
        )).run()


bot.add_cog(Leveling(bot))
bot.run("token")