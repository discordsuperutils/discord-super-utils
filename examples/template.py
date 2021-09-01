import aiosqlite
from discord.ext import commands

import discordSuperUtils

bot = commands.Bot(command_prefix="-")
TemplateManager = discordSuperUtils.TemplateManager(bot)


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(...)
    await TemplateManager.connect_to_database(database,
                                              ['templates', 'categories', 'text_channels', 'voice_channels', 'roles'])
    print('Template manager is ready.', bot.user)


@bot.command()
async def get_template(ctx, template_id: str):
    print(await TemplateManager.get_template(template_id))


@bot.command()
async def create_template(ctx):
    await TemplateManager.create_template(ctx.guild)


bot.run("token")
