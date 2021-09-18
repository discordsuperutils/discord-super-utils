from discord.ext import commands

import discordSuperUtils
from discordSuperUtils import MusicManager
import discord

client_id = ""
client_secret = ""

bot = commands.Bot(command_prefix="-")
MusicManager = MusicManager(
    bot, spotify_support=True, client_id=client_id, client_secret=client_secret
)


# MusicManager = MusicManager(bot, client_id=client_id,
#                                   client_secret=client_secret, spotify_support=True)

# if using spotify support use this instead ^^^


@MusicManager.event()
async def on_music_error(ctx, error):
    raise error  # add your error handling here! Errors are listed in the documentation.


@MusicManager.event()
async def on_queue_end(ctx):
    print(f"The queue has ended in {ctx}")
    # You could wait and check activity, etc...


@MusicManager.event()
async def on_inactivity_disconnect(ctx):
    print(f"I have left {ctx} due to inactivity..")


@MusicManager.event()
async def on_play(ctx, player):
    await ctx.send(f"Playing {player}")


@bot.event
async def on_ready():
    print("Music manager is ready.", bot.user)


@bot.command()
async def leave(ctx):
    if await MusicManager.leave(ctx):
        await ctx.send("Left Voice Channel")


@bot.command()
async def np(ctx):
    if player := await MusicManager.now_playing(ctx):
        duration_played = await MusicManager.get_player_played_duration(ctx, player)
        # You can format it, of course.

        await ctx.send(
            f"Currently playing: {player}, \n"
            f"Duration: {duration_played}/{player.duration}"
        )


@bot.command()
async def join(ctx):
    if await MusicManager.join(ctx):
        await ctx.send("Joined Voice Channel")


@bot.command()
async def play(ctx, *, query: str):
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        await MusicManager.join(ctx)

    async with ctx.typing():
        players = await MusicManager.create_player(query, ctx.author)

    if players:
        if await MusicManager.queue_add(
            players=players, ctx=ctx
        ) and not await MusicManager.play(ctx):
            await ctx.send("Added to queue")

    else:
        await ctx.send("Query not found.")


@bot.command()
async def lyrics(ctx, query: str = None):
    if response := await MusicManager.lyrics(ctx, query):
        title, author, query_lyrics = response

        splitted = query_lyrics.split("\n")
        res = []
        current = ""
        for i, split in enumerate(splitted):
            if len(splitted) <= i + 1 or len(current) + len(splitted[i + 1]) > 1024:
                res.append(current)
                current = ""
                continue
            current += split + "\n"

        page_manager = discordSuperUtils.PageManager(
            ctx,
            [
                discord.Embed(
                    title=f"Lyrics for '{title}' by '{author}', (Page {i + 1}/{len(res)})",
                    description=x,
                )
                for i, x in enumerate(res)
            ],
            public=True,
        )
        await page_manager.run()
    else:
        await ctx.send("No lyrics found.")


@bot.command()
async def pause(ctx):
    if await MusicManager.pause(ctx):
        await ctx.send("Player paused.")


@bot.command()
async def resume(ctx):
    if await MusicManager.resume(ctx):
        await ctx.send("Player resumed.")


@bot.command()
async def volume(ctx, volume: int):
    await MusicManager.volume(ctx, volume)


@bot.command()
async def loop(ctx):
    is_loop = await MusicManager.loop(ctx)
    await ctx.send(f"Looping toggled to {is_loop}")


@bot.command()
async def shuffle(ctx):
    is_shuffle = await MusicManager.shuffle(ctx)
    await ctx.send(f"Shuffle toggled to {is_shuffle}")


@bot.command()
async def autoplay(ctx):
    is_autoplay = await MusicManager.autoplay(ctx)
    await ctx.send(f"Autoplay toggled to {is_autoplay}")


@bot.command()
async def queueloop(ctx):
    is_loop = await MusicManager.queueloop(ctx)
    await ctx.send(f"Queue looping toggled to {is_loop}")


@bot.command()
async def history(ctx):
    formatted_history = [
        f"Title: '{x.title}'\nRequester: {x.requester.mention}"
        for x in (await MusicManager.get_queue(ctx)).history
    ]

    embeds = discordSuperUtils.generate_embeds(
        formatted_history,
        "Song History",
        "Shows all played songs",
        25,
        string_format="{}",
    )

    page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
    await page_manager.run()


@bot.command()
async def skip(ctx, index: int = None):
    await MusicManager.skip(ctx, index)


@bot.command()
async def queue(ctx):
    formatted_queue = [
        f"Title: '{x.title}\nRequester: {x.requester.mention}"
        for x in (await MusicManager.get_queue(ctx)).queue
    ]

    embeds = discordSuperUtils.generate_embeds(
        formatted_queue,
        "Queue",
        f"Now Playing: {await MusicManager.now_playing(ctx)}",
        25,
        string_format="{}",
    )

    page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
    await page_manager.run()


@bot.command()
async def ls(ctx):
    if queue := await MusicManager.get_queue(ctx):
        loop = queue.loop
        loop_status = None

        if loop == discordSuperUtils.Loops.LOOP:
            loop_status = "Looping enabled."

        elif loop == discordSuperUtils.Loops.QUEUE_LOOP:
            loop_status = "Queue looping enabled."

        elif loop == discordSuperUtils.Loops.NO_LOOP:
            loop_status = "No loop enabled."

        if loop_status:
            await ctx.send(loop_status)


bot.run("token")
