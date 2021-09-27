from __future__ import annotations

import os
import textwrap
from enum import Enum
from io import BytesIO
from typing import Optional, Tuple, Union, TYPE_CHECKING

import PIL
import PIL.ImageShow
import aiohttp
import discord
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont

if TYPE_CHECKING:
    from .leveling import LevelingAccount


__all__ = ("ImageManager", "Backgrounds")


class ImageManager:
    """
    An image manager that manages picture creation.
    """

    __slots__ = ()

    DEFAULT_COLOR = (127, 255, 0)

    @staticmethod
    def load_asset(name: str) -> str:
        return os.path.join(os.path.dirname(__file__), "assets", name)

    @staticmethod
    async def make_request(url: str) -> Optional[bytes]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.read()

    @classmethod
    async def convert_image(cls, url: str) -> Image:
        return PIL.Image.open(BytesIO(await cls.make_request(url))).convert("RGBA")

    @staticmethod
    def human_format(num):
        original_num = num

        num = float("{:.3g}".format(num))
        magnitude = 0
        matches = ["", "K", "M", "B", "T", "Qua", "Qui"]
        while abs(num) >= 1000:
            if magnitude >= 5:
                break

            magnitude += 1
            num /= 1000.0

        try:
            return "{}{}".format(
                "{:f}".format(num).rstrip("0").rstrip("."), matches[magnitude]
            )
        except IndexError:
            return original_num

    @staticmethod
    def multiline_text(
        card: Image.Image,
        text: str,
        font: FreeTypeFont,
        text_color: Tuple[int, int, int],
        start_height: Union[int, float],
        width: int,
    ) -> None:
        """
        Draws multiline text on the card.

        :param Image.Image card: The card to draw on.
        :param str text: The text to write.
        :param FreeTypeFont font: The font.
        :param Tuple[int, int, int] text_color: The text color.
        :param Union[int, float] start_height:
            The start height of the text, the text will start there, and make its way downwards.
        :param int width: The width of the wrap.
        :return: None
        :rtype: None
        """

        draw = ImageDraw.Draw(card)
        image_width, image_height = card.size

        y_text = start_height
        lines = textwrap.wrap(text, width=width)

        for line in lines:
            line_width, line_height = font.getsize(line)

            draw.text(
                ((image_width - line_width) / 2, y_text),
                line,
                font=font,
                fill=text_color,
            )

            y_text += line_height

    async def draw_profile_picture(
        self,
        card: Image,
        member: discord.Member,
        location: Tuple[int, int],
        size: int = 180,
        outline_thickness: int = 5,
        status: bool = True,
        outline_color: Tuple[int, int, int] = (255, 255, 255),
    ):
        blank = Image.new("RGBA", card.size, (255, 255, 255, 0))

        location = tuple(
            round(x - size / 2) if i <= 1 else round(x + size / 2)
            for i, x in enumerate(location + location)
        )

        outline_dimensions = tuple(
            x - outline_thickness if i <= 1 else x + outline_thickness
            for i, x in enumerate(location)
        )

        size_dimensions = (size, size)
        status_dimensions = tuple(round(x / 4) for x in size_dimensions)

        mask = Image.new("RGBA", card.size, 0)
        ImageDraw.Draw(mask).ellipse(location, fill=(255, 25, 255, 255))

        avatar = (await self.convert_image(str(member.avatar_url))).resize(
            size_dimensions
        )
        profile_pic_holder = Image.new("RGBA", card.size, (255, 255, 255, 255))

        ImageDraw.Draw(card).ellipse(outline_dimensions, fill=outline_color)

        profile_pic_holder.paste(avatar, location)
        pre_card = Image.composite(profile_pic_holder, card, mask)
        pre_card = pre_card.convert("RGBA")

        if status:
            status_picture = Image.open(self.load_asset(f"{member.status.name}.png"))
            status_picture = status_picture.convert("RGBA").resize(status_dimensions)

            blank.paste(
                status_picture, tuple(x - status_dimensions[0] for x in location[2:])
            )

        return Image.alpha_composite(pre_card, blank)

    async def create_welcome_card(
        self,
        member: discord.Member,
        background: Union[Backgrounds, str],
        title: str,
        description: str,
        title_color: Tuple[int, int, int] = (255, 255, 255),
        description_color: Tuple[int, int, int] = (255, 255, 255),
        font_path: str = None,
        outline: int = 5,
        transparency: Optional[int] = 0,
    ) -> discord.File:
        result_bytes = BytesIO()

        card = (
            Image.open(background.value)
            if isinstance(background, Backgrounds)
            else await self.convert_image(background)
        )
        card = card.resize((1024, 500))

        font_path = font_path if font_path else self.load_asset("font.ttf")

        big_font = ImageFont.truetype(font_path, 36)
        small_font = ImageFont.truetype(font_path, 30)

        draw = ImageDraw.Draw(card, "RGBA")
        if transparency:
            draw.rectangle((30, 30, 994, 470), fill=(0, 0, 0, transparency))

        draw.text((512, 360), title, title_color, font=big_font, anchor="ms")
        self.multiline_text(card, description, small_font, description_color, 380, 60)

        final_card = await self.draw_profile_picture(
            card, member, (512, 180), 260, outline_thickness=outline
        )

        final_card.save(result_bytes, format="PNG")
        result_bytes.seek(0)
        return discord.File(result_bytes, filename="welcome_card.png")

    async def create_leveling_profile(
        self,
        member: discord.Member,
        member_account: LevelingAccount,
        background: Union[Backgrounds, str],
        rank: int,
        name_color: Tuple[int, int, int] = DEFAULT_COLOR,
        rank_color: Tuple[int, int, int] = DEFAULT_COLOR,
        level_color: Tuple[int, int, int] = DEFAULT_COLOR,
        xp_color: Tuple[int, int, int] = DEFAULT_COLOR,
        bar_outline_color: Tuple[int, int, int] = (255, 255, 255),
        bar_fill_color: Tuple[int, int, int] = DEFAULT_COLOR,
        bar_blank_color: Tuple[int, int, int] = (255, 255, 255),
        profile_outline_color: Tuple[int, int, int] = DEFAULT_COLOR,
        font_path: str = None,
        outline: int = 5,
    ) -> discord.File:
        result_bytes = BytesIO()

        card = (
            Image.open(background.value)
            if isinstance(background, Backgrounds)
            else await self.convert_image(background)
        )
        card = card.resize((850, 238))

        font_path = font_path if font_path else self.load_asset("font.ttf")
        font_big = ImageFont.truetype(font_path, 36)
        font_medium = ImageFont.truetype(font_path, 30)
        font_normal = ImageFont.truetype(font_path, 25)
        font_small = ImageFont.truetype(font_path, 20)

        draw = ImageDraw.Draw(card)
        draw.text((245, 90), str(member), name_color, font=font_big, anchor="ls")
        draw.text((800, 90), f"Rank #{rank}", rank_color, font=font_medium, anchor="rs")
        draw.text(
            (245, 165),
            f"Level {await member_account.level()}",
            level_color,
            font=font_normal,
            anchor="ls",
        )
        draw.text(
            (800, 165),
            f"{self.human_format(await member_account.xp())} /"
            f" {self.human_format(await member_account.next_level())} XP",
            xp_color,
            font=font_small,
            anchor="rs",
        )

        draw.rounded_rectangle(
            (242, 182, 803, 208),
            fill=bar_blank_color,
            outline=bar_outline_color,
            radius=13,
            width=3,
        )

        length_of_bar = await member_account.percentage_next_level() * 5.5 + 250
        draw.rounded_rectangle(
            (245, 185, length_of_bar, 205), fill=bar_fill_color, radius=10
        )

        final_card = await self.draw_profile_picture(
            card,
            member,
            (109, 119),
            outline_thickness=outline,
            outline_color=profile_outline_color,
        )

        final_card.save(result_bytes, format="PNG")
        result_bytes.seek(0)
        return discord.File(result_bytes, filename="rankcard.png")


class Backgrounds(Enum):
    GALAXY = ImageManager.load_asset("1.png")
    BLANK_GRAY = ImageManager.load_asset("2.png")
    GAMING = ImageManager.load_asset("3.png")
