from datetime import datetime, timezone

import discord
import pytz
from discord.ext import commands

import discordSuperUtils

bot = commands.Bot(command_prefix="-", intents=discord.Intents.all())
BirthdayManager = discordSuperUtils.BirthdayManager(bot)


def ordinal(num: int) -> str:
    """
    Returns the ordinal representation of a number

    Examples:
        11: 11th
        13: 13th
        14: 14th
        3: 3rd
        5: 5th

    :param num:
    :return:
    """

    return f"{num}th" if 11 <= (num % 100) <= 13 else f"{num}{['th', 'st', 'nd', 'rd', 'th'][min(num % 10, 4)]}"


@BirthdayManager.event()
async def on_member_birthday(birthday_member):
    # Incase you want to support multiple guilds, you must create a channel system.
    # For example, to create a channel system you can make a "set_birthday_channel" command, and in on_member_birthday,
    # you can fetch the same channel and send birthday updates there.
    # Hard coding the channel ID into your code will work, but only on ONE guild (specifically, where the same channel
    # is located) other guilds wont have the same channel, meaning it wont send them birthday updates.
    # I advise of making a channel system, I do not recommend hard coding channel IDs at all unless you are SURE
    # the channel IDs wont be changed and the bot is not supposed to work on other guilds.
    channel = birthday_member.member.guild.get_channel(...)

    if channel:
        embed = discord.Embed(
            title="Happy birthday!",
            description=f"Happy {ordinal(await birthday_member.age())} birthday, {birthday_member.member.mention}!",
            color=0x00ff00
        )

        embed.set_thumbnail(url=birthday_member.member.avatar_url)

        await channel.send(content=birthday_member.member.mention, embed=embed)


@bot.event
async def on_ready():
    database = discordSuperUtils.DatabaseManager.connect(...)
    await BirthdayManager.connect_to_database(database, ["birthdays"])

    print('Birthday manager is ready.', bot.user)


@bot.command()
async def upcoming(ctx):
    guild_upcoming = await BirthdayManager.get_upcoming(ctx.guild)
    formatted_upcoming = [
        f"Member: {x.member}, Age: {await x.age()}, Date of Birth: {(await x.birthday_date()):'%b %d %Y'}" for x in
        guild_upcoming]

    await discordSuperUtils.PageManager(ctx, discordSuperUtils.generate_embeds(
        formatted_upcoming,
        title="Upcoming Birthdays",
        fields=25,
        description=f"Upcoming birthdays in {ctx.guild}"
    )).run()


@bot.command()
async def birthday(ctx, member: discord.Member = None):
    member = member or ctx.author

    member_birthday = await BirthdayManager.get_birthday(member)

    if not member_birthday:
        await ctx.send("The specified member does not have a birthday setup!")
        return

    embed = discord.Embed(
        title=f"{member}'s Birthday",
        color=0x00ff00
    )

    embed.add_field(
        name="Birthday",
        value=(await member_birthday.birthday_date()).strftime('%b %d %Y'),
        inline=False
    )

    embed.add_field(
        name="Timezone",
        value=await member_birthday.timezone(),
        inline=False
    )

    embed.add_field(
        name="Age",
        value=str(await member_birthday.age()),
        inline=False
    )

    await ctx.send(embed=embed)


@bot.command()
async def setup_birthday(ctx):
    questions = [
        "What year where you born in?",
        "What month where you born in?",
        "What day of month where you born in?",
        "What is your timezone? List: https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568"
        "\nAlternatively, you can use the timezone picker: "
        "http://scratch.andrewl.in/timezone-picker/example_site/openlayers_example.html"
    ]
    # BirthdayManager uses pytz to save timezones and not raw UTC offsets, why?
    # well, simply, using UTC offsets will result in a lot of confusion. The user might pass an incorrect UTC offset
    # and he cloud be wished a happy birthday before his birthday. (The UTC offsets might have issues with DST, too!)
    # that's why we chose pytz, to make custom timezones user-friendly and easy to setup.

    answers, timed_out = await discordSuperUtils.questionnaire(ctx, questions, member=ctx.author)
    # The questionnaire supports embeds.

    if timed_out:
        await ctx.send("You have timed out.")
        return

    for answer in answers[:-1]:
        if not answer.isnumeric():
            await ctx.send("Setup failed.")
            return

        i = answers.index(answer)
        answers[i] = int(answer)

    if answers[3] not in pytz.all_timezones:
        await ctx.send("Setup failed, timezone not found.")
        return

    try:
        now = datetime.now(tz=timezone.utc)
        date_of_birth = datetime(*answers[:-1], tzinfo=timezone.utc)
        if date_of_birth > now:
            await ctx.send("Setup failed, your date of birth is in the future.")
            return
    except ValueError:
        await ctx.send("Setup failed.")
        return

    member_birthday = await BirthdayManager.get_birthday(ctx.author)
    if member_birthday:
        await member_birthday.set_birthday_date(date_of_birth.timestamp())
        await member_birthday.set_timezone(answers[3])
    else:
        await BirthdayManager.create_birthday(ctx.author, date_of_birth.timestamp(), answers[3])

    await ctx.send(f"Successfully set your birthday to {date_of_birth:%b %d %Y}.")


bot.run("token")
