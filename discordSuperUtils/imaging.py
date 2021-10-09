from __future__ import annotations

import datetime
import os
import textwrap
import time
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
        """
        Returns the asset path of the asset.

        :param str name: The asset.
        :return: The asset path.
        :rtype: str
        """

        return os.path.join(os.path.dirname(__file__), "assets", name)

    @staticmethod
    async def make_request(url: str) -> Optional[bytes]:
        """
        Returns the bytes of the URL response, if applicable.

        :param str url: The url.
        :return: The response bytes.
        :rtype: Optional[bytes]
        """

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.read()

    @classmethod
    async def convert_image(cls, url: str) -> Image.Image:
        """
        Converts the image to a PIL image.

        :param str url: The URL.
        :return: The converted image.
        :rtype: Image.Image
        """

        return PIL.Image.open(BytesIO(await cls.make_request(url))).convert("RGBA")

    @staticmethod
    def human_format(num: int) -> str:
        """
        Converts the number to a human readable format.

        :param int num: The number.
        :return: The human readable format.
        :rtype: str
        """

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
            return str(original_num)

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
        card: Image.Image,
        member: discord.Member,
        location: Tuple[int, int],
        size: int = 180,
        outline_thickness: int = 5,
        status: bool = True,
        outline_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> Image.Image:
        """
        |coro|

        Pastes the profile picture on the card.

        :param Image.Image card: The card.
        :param discord.Member member: The member to get the profile picture from.
        :param Tuple[int, int] location: The center of the picture.
        :param int size: The size of the pasted profile picture.
        :param int outline_thickness: The outline thickness.
        :param bool status: A bool indicating if it should paste the member's status icon.
        :param Tuple[int, int, int] outline_color: The outline color.
        :return: The result image.
        :rtype: Image.Image
        """

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
        transparency: int = 0,
    ) -> discord.File:
        """
        |coro|

        Creates a welcome image for the member and returns it as a discord.File.

        :param discord.Member member: The joined member.
        :param Union[Backgrounds, str] background: The background of the image, can be a Backgrounds enum or a URL.
        :param str title: The title.
        :param str description: The description.
        :param Tuple[int, int, int] title_color: The color of the title.
        :param Tuple[int, int, int] description_color: The color of the description.
        :param str font_path: The font path, uses the default font if not passed.
        :param int outline: The outline thickness.
        :param int transparency: The transparency of the background made.
        :return: The discord file.
        :rtype: discord.File
        """

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
        if transparency and isinstance(background, Backgrounds):
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
        """
        |coro|

        Creates a leveling image, converted to a discord.File.

        :param discord.Member member: The member.
        :param LevelingAccount member_account: The leveling account of the member.
        :param Union[Backgrounds, str] background: The background of the image.
        :param int rank: The guild rank of the member.
        :param Tuple[int, int, int] name_color: The color of the member's name.
        :param Tuple[int, int, int] rank_color: The color of the member's rank.
        :param Tuple[int, int, int] level_color: The color of the member's level.
        :param Tuple[int, int, int] xp_color: The color of the member's xp.
        :param Tuple[int, int, int] bar_outline_color: The color of the member's progress bar outline.
        :param Tuple[int, int, int] bar_fill_color: The color of the member's progress bar fill.
        :param Tuple[int, int, int] bar_blank_color: The color of the member's progress bar blank.
        :param Tuple[int, int, int] profile_outline_color: The color of the member's outliine.
        :param str font_path: The font path, uses the default font if not passed.
        :param int outline: The outline thickness.
        :return: The image, converted to a discord.File.
        :rtype: discord.File
        """

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

    async def create_spotify_card(
        self, spotify_activity: discord.Spotify, font_path: str = None
    ) -> discord.File:
        """
        |coro|

        Creates a Spotify activity image for the Spotify song and returns it as a discord.File.

        :param discord.Spotify spotify_activity: The Spotify activity.
        :param str font_path: The font path, uses the default font if not passed.
        :return: The discord file.
        :rtype: discord.File
        """

        result_bytes = BytesIO()

        album_image = await self.convert_image(spotify_activity.album_cover_url)

        # Background colour
        paletted = album_image.convert(
            "P", palette=Image.ADAPTIVE, colors=1
        )  # Reduce to palette
        # Finding dominant background color
        palette = paletted.getpalette()
        color_counts = paletted.getcolors()
        palette_index = color_counts[0][1]
        dominant_color = tuple(palette[palette_index * 3 : palette_index * 3 + 3])

        # Checking brightness of bg color
        brightness = (
            (0.21 * dominant_color[0])
            + (0.72 * dominant_color[1])
            + (0.07 * dominant_color[2])
        )

        if brightness < 100:
            text_color = "white"
            bg_img = "spotify_white.png"
        else:
            text_color = "black"
            bg_img = "spotify_black.png"

        track_background_image = Image.open(self.load_asset(bg_img))

        font_path = font_path if font_path else self.load_asset("font.ttf")

        # Fonts
        title_font = ImageFont.truetype(font_path, 16)
        artist_font = ImageFont.truetype(font_path, 14)
        album_font = ImageFont.truetype(font_path, 14)
        start_duration_font = ImageFont.truetype(font_path, 12)
        end_duration_font = ImageFont.truetype(font_path, 12)

        # Positions
        title_text_position = 150, 30
        artist_text_position = 150, 60
        album_text_position = 150, 80
        start_duration_text_position = 150, 119
        end_duration_text_position = 508, 119

        played_duration = (
            datetime.datetime.utcnow() - spotify_activity.start
        ).total_seconds()
        total_duration = spotify_activity.duration.total_seconds()

        played = played_duration / total_duration

        start_duration = time.strftime("%H:%M:%S", time.gmtime(played_duration))
        end_duration = time.strftime("%H:%M:%S", time.gmtime(total_duration))

        # Draws
        draw_on_image = ImageDraw.Draw(track_background_image)

        draw_on_image.text(
            title_text_position, spotify_activity.title, text_color, font=title_font
        )

        draw_on_image.text(
            artist_text_position,
            f"by {spotify_activity.artist}",
            text_color,
            font=artist_font,
        )

        draw_on_image.text(
            album_text_position, spotify_activity.album, text_color, font=album_font
        )

        draw_on_image.text(
            start_duration_text_position,
            start_duration,
            text_color,
            font=start_duration_font,
        )

        draw_on_image.text(
            end_duration_text_position, end_duration, text_color, font=end_duration_font
        )

        draw_on_image.rounded_rectangle(
            (198, 125, 198 + 300 * played, 129),
            fill=text_color,
            outline=None,
            radius=3,
            width=0,
        )

        background_image_color = Image.new(
            "RGBA", track_background_image.size, dominant_color
        )
        background_image_color.paste(
            track_background_image, (0, 0), track_background_image
        )

        # Resize
        album_image_resize = album_image.resize((140, 160))
        background_image_color.paste(album_image_resize, (0, 0), album_image_resize)

        # Save image
        background_image_color.convert("RGB")

        background_image_color.save(result_bytes, format="PNG")
        result_bytes.seek(0)
        return discord.File(result_bytes, filename="spotify.png")


class Backgrounds(Enum):
    GALAXY = ImageManager.load_asset("1.png")
    BLANK_GRAY = ImageManager.load_asset("2.png")
    GAMING = ImageManager.load_asset("3.png")
