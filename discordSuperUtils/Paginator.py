import asyncio
from math import ceil
import discord


def generate_embeds(list_to_generate, title, description, fields, string_format):
    num_of_embeds = ceil((len(list_to_generate) + 1) / fields)

    embeds = [
        discord.Embed(
            title=f"{title} (Page 1/{num_of_embeds})",
            description=description,
            color=0xff0000
        )
    ]

    for i in range(2, num_of_embeds + 1):
        embeds.append(discord.Embed(
            title=f"{title} (Page {i}/{num_of_embeds})",
            color=0xff0000
        )
        )

    embed_index = 0
    for index, element in enumerate(list_to_generate):
        embeds[embed_index].add_field(name=f"**{index + 1}.**",
                                      value=string_format.format(element),
                                      inline=False)

        if (index + 1) % fields == 0:
            embed_index += 1

    return embeds


class EmojiError(Exception):
    pass


class PageManager:
    def __init__(self, ctx, messages, timeout=60, emojis=None, public=False, index=0):
        self.ctx = ctx
        self.messages = messages
        self.timeout = timeout
        self.emojis = emojis if emojis is not None else ["⏪", "◀️", "▶️", "⏩"]
        self.public = public
        self.index = index

    async def run(self):
        if len(self.emojis) != 4:
            raise EmojiError(f"Passed {len(self.emojis)} emojis when 4 are needed.")

        self.index = 0 if not -1 < self.index < len(self.messages) else self.index

        message_to_send = self.messages[self.index]
        if isinstance(message_to_send, discord.Embed):
            message = await self.ctx.send(embed=message_to_send)
        else:
            message = await self.ctx.send(message_to_send)

        for emoji in self.emojis:
            await message.add_reaction(emoji)

        while True:
            try:
                reaction, user = await self.ctx.bot.wait_for('reaction_add',
                                                             check=lambda x, y: x.message == message,
                                                             timeout=self.timeout)

                if user.bot:
                    continue

                if user != self.ctx.author and not self.public:
                    continue

            except asyncio.TimeoutError:
                break

            if reaction.emoji == self.emojis[0]:
                self.index = 0

            elif reaction.emoji == self.emojis[1]:
                if self.index > 0:
                    self.index -= 1

            elif reaction.emoji == self.emojis[2]:
                if self.index < len(self.messages) - 1:
                    self.index += 1

            elif reaction.emoji == self.emojis[3]:
                self.index = len(self.messages) - 1

            await message.remove_reaction(reaction.emoji, user)
            message_to_send = self.messages[self.index]

            if isinstance(message_to_send, discord.Embed):
                await message.edit(embed=message_to_send, content=None)
            else:
                await message.edit(content=message_to_send, embed=None)