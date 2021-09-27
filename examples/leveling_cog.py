import discord
from discord.ext import commands

import discordSuperUtils

bot = commands.Bot(command_prefix="-", intents=discord.Intents.all())


class Leveling(commands.Cog, discordSuperUtils.CogManager.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.LevelingManager = discordSuperUtils.LevelingManager(bot, award_role=True)
        self.ImageManager = discordSuperUtils.ImageManager()
        super().__init__()  # Make sure you define your managers before running CogManager.Cog's __init__ function.
        # Incase you do not, CogManager.Cog wont find the managers and will not link them to the events.
        # Alternatively, you can pass your managers in CogManager.Cog's __init__ function incase you are using the same
        # managers in different files, I recommend saving the managers as attributes on the bot object, instead of
        # importing them.

    @commands.Cog.listener()
    async def on_ready(self):
        database = discordSuperUtils.DatabaseManager.connect(...)
        await self.LevelingManager.connect_to_database(
            database, ["xp", "roles", "role_list"]
        )

        print("Leveling manager is ready.", bot.user)

    @discordSuperUtils.CogManager.event(discordSuperUtils.LevelingManager)
    async def on_level_up(self, message, member_data, roles):
        await message.reply(
            f"You are now level {await member_data.level()}"
            + (f", you have received the {roles[0]}" f" role." if roles else "")
        )

    @commands.command()
    async def rank(self, ctx, member: discord.Member = None):
        mem_obj = member if member else ctx.author
        member_data = await self.LevelingManager.get_account(mem_obj)

        if not member_data:
            await ctx.send(
                f"I am still creating your account! please wait a few seconds."
            )
            return

        guild_leaderboard = await self.LevelingManager.get_leaderboard(ctx.guild)
        member = [x for x in guild_leaderboard if x.member == mem_obj]
        member_rank = guild_leaderboard.index(member[0]) + 1 if member else -1

        image = await self.ImageManager.create_leveling_profile(
            member=mem_obj,
            member_account=member_data,
            background=discordSuperUtils.Backgrounds.GALAXY,
            # name_color=(255, 255, 255),
            # rank_color=(127, 255, 0),
            # level_color=(255, 255, 255),
            # xp_color=(255, 255, 255),
            # bar_outline_color=(255, 255, 255),
            # bar_fill_color=(127, 255, 0),
            # bar_blank_color=(72, 75, 78),
            # profile_outline_color=(100, 100, 100),
            rank=member_rank,
            font_path=None,
            outline=5,
        )

        await ctx.send(file=image)

    @commands.command()
    async def set_roles(self, ctx, interval: int, *roles: discord.Role):
        await self.LevelingManager.set_interval(ctx.guild, interval)
        await self.LevelingManager.set_roles(ctx.guild, roles)

        await ctx.send(
            f"Successfully set the interval to {interval} and role list to {', '.join(role.name for role in roles)}"
        )

    @commands.command()
    async def leaderboard(self, ctx):
        guild_leaderboard = await self.LevelingManager.get_leaderboard(ctx.guild)
        formatted_leaderboard = [
            f"Member: {x.member}, XP: {await x.xp()}" for x in guild_leaderboard
        ]

        await discordSuperUtils.PageManager(
            ctx,
            discordSuperUtils.generate_embeds(
                formatted_leaderboard,
                title="Leveling Leaderboard",
                fields=25,
                description=f"Leaderboard of {ctx.guild}",
            ),
        ).run()


bot.add_cog(Leveling(bot))
bot.run("token")
