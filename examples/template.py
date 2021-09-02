from discord.ext import commands

import discordSuperUtils

bot = commands.Bot(command_prefix="-")
TemplateManager = discordSuperUtils.TemplateManager(bot)


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(...)
    await TemplateManager.connect_to_database(database,
                                              ['templates',
                                               'categories',
                                               'text_channels',
                                               'voice_channels',
                                               'roles',
                                               'overwrites'])
    print('Template manager is ready.', bot.user)


@bot.command()
async def apply_template(ctx, template_id: str):
    template = await TemplateManager.get_template(template_id)
    await template.apply(ctx.guild)


@bot.command()
async def get_template(ctx, template_id: str):
    print(await TemplateManager.get_template(template_id))


@bot.command()
async def create_template(ctx):
    template = await TemplateManager.create_template(ctx.guild)
    await ctx.send(f"Created template with id {template.info.template_id}")


bot.run("token")
