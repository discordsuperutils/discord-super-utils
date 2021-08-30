from __future__ import annotations

import os
from enum import Enum
from io import BytesIO
from typing import (
    Optional,
    Tuple,
    Union,
    TYPE_CHECKING
)

import PIL
import PIL.ImageShow
import aiohttp
import discord
from PIL import Image, ImageFont, ImageDraw

if TYPE_CHECKING:
    from .Leveling import LevelingAccount


class ImageManager:
    @staticmethod
    def load_asset(name: str) -> str:
        return os.path.join(os.path.dirname(__file__), 'assets', name)

    @staticmethod
    async def make_request(url: str) -> Optional[bytes]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.read()

    @classmethod
    async def convert_image(cls, url: str) -> Image:
        return PIL.Image.open(BytesIO(await cls.make_request(url))).convert('RGBA')

    @classmethod
    def human_format(cls, num):
        original_num = num

        num = float('{:.3g}'.format(num))
        magnitude = 0
        matches = ['', 'K', 'M', 'B', 'T', 'Qua', 'Qui']
        while abs(num) >= 1000:
            if magnitude >= 5:
                break

            magnitude += 1
            num /= 1000.0

        try:
            return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), matches[magnitude])
        except IndexError:
            return original_num

    async def merge_image(self,
                          foreground: str,
                          background: str,
                          blend_level: float = 0.6,
                          discord_file: bool = True) -> Union[discord.File, Image]:
        """Merges two images together"""
        foreground = await self.convert_image(foreground)
        background = await self.convert_image(background)
        result_bytes = BytesIO()
        width, height = background.size

        foreground = foreground.resize((width, height), PIL.Image.ANTIALIAS)
        result = PIL.Image.blend(background, foreground, alpha=blend_level)

        if discord_file:
            result.save(result_bytes, format="PNG")
            result_bytes.seek(0)
            return discord.File(result_bytes, filename="mergedimage.png")

        return result

    async def create_leveling_profile(self,
                                      member: discord.Member,
                                      member_account: LevelingAccount,
                                      background: Backgrounds,
                                      text_color: Tuple[int, int, int],
                                      rank: int,
                                      font_path: str = None,
                                      outline: bool = True) -> discord.File:
        result_bytes = BytesIO()

        card = Image.open(background.value).resize((900, 238))

        avatar = (await self.convert_image(str(member.avatar_url))).resize((180, 180))
        profile_pic_holder = Image.new("RGBA", card.size, (255, 255, 255, 255))
        status = Image.open(self.load_asset(f"{member.status.name}.png")).convert("RGBA").resize((55, 55))

        font_path = font_path if font_path else self.load_asset("font.ttf")
        font_big = ImageFont.truetype(font_path, 36)
        font_small = ImageFont.truetype(font_path, 20)

        mask = Image.new("RGBA", card.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((29, 29, 209, 209), fill=(255, 25, 255, 255))

        draw = ImageDraw.Draw(card)
        draw.text((245, 60), str(member), text_color, font=font_big)
        draw.text((620, 60), f"Rank #{rank}", text_color, font=font_big)
        draw.text((245, 145), f"Level {await member_account.level()}", text_color, font=font_small)
        draw.text((625, 145),
                  f"{self.human_format(await member_account.xp())} "
                  f" {self.human_format(await member_account.next_level())} XP",
                  text_color,
                  font=font_small)

        blank = Image.new("RGBA", card.size, (255, 255, 255, 0))
        blank_draw = ImageDraw.Draw(blank)
        blank_draw.rounded_rectangle((245, 185, 750, 205), fill=(255, 255, 255, 0), outline=text_color, radius=10)

        length_of_bar = (await member_account.percentage_next_level() * 4.9) + 248

        blank_draw.rounded_rectangle((248, 188, length_of_bar, 202), fill=text_color, radius=7)

        if outline:
            draw.ellipse((24, 24, 214, 214), fill='white', outline='white')

        profile_pic_holder.paste(avatar, (29, 29, 209, 209))
        pre_card = Image.composite(profile_pic_holder, card, mask)
        pre_card = pre_card.convert('RGBA')
        pre_card = Image.alpha_composite(pre_card, blank)

        blank = Image.new("RGBA", card.size, (255, 255, 255, 0))
        blank.paste(status, (155, 155))
        final_card = Image.alpha_composite(pre_card, blank)

        final_card.save(result_bytes, format="PNG")
        result_bytes.seek(0)
        return discord.File(result_bytes, filename="rankcard.png")


class Backgrounds(Enum):
    GALAXY = ImageManager.load_asset("1.png")
    BLANK_GRAY = ImageManager.load_asset("2.png")
    GAMING = ImageManager.load_asset("3.png")
