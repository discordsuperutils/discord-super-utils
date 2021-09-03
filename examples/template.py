import aiosqlite
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
    # Check permissions here.
    template = await TemplateManager.get_template(template_id)
    if not template:
        await ctx.send("Template has not been found.")
        return

    await ctx.send(f"Applying template {template.info.template_id}")
    await template.apply(ctx.guild)


@bot.command()
async def delete_template(ctx, template_id: str):
    template = await TemplateManager.get_template(template_id)
    # Here, you could check permissions, I recommend checking if ctx is the template guild.
    if not template:
        await ctx.send("Template has not been found.")
        return

    partial_template = await template.delete()
    await ctx.send(f"Deleted template with id {partial_template.info.template_id}")


@bot.command()
async def get_guild_templates(ctx):
    templates = await TemplateManager.get_templates(ctx.guild)
    await ctx.send(templates)


@bot.command()
async def get_templates(ctx):
    templates = await TemplateManager.get_templates()
    await ctx.send(templates)
    # Remember you can format these templates into embeds etc..


@bot.command()
async def get_template(ctx, template_id: str):
    template = await TemplateManager.get_template(template_id)
    if not template:
        await ctx.send("Template has not been found.")
        return

    await ctx.send(f"Template found: {template}")


@bot.command()
async def create_template(ctx):
    # Again, you should check permissions here to make sure this isn't abused.
    # You can also get all the templates a guild has, using TemplateManager.get_templates
    template = await TemplateManager.create_template(ctx.guild)
    await ctx.send(f"Created template with id {template.info.template_id}")


bot.run("token")
