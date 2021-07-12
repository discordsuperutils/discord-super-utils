import PIL
import PIL.ImageShow
import aiohttp  # koyashie fix unused / duplicate imports
import discord
import os
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO


class ImageManager:
    def __init__(self, bot, txt_colour=None, card_back=1, custom_card_back: bool = False):
        self.bot = bot
        txt_colour = (80, 92, 112) if not txt_colour else txt_colour
        self.txt_colour = txt_colour  # tuple with rgb colour
        self.default_bg = self.fetch_card_back(card_back, custom_card_back)
        self.online = self.load_asset('online.png')
        self.offline = self.load_asset('offline.png')
        self.idle = self.load_asset('idle.png')
        self.dnd = self.load_asset('dnd.png')
        self.streaming = self.load_asset('streaming.png')
        self.font = self.load_asset('font.ttf')
        self.bk = self.load_asset('grey.png')

    @classmethod
    def load_asset(cls, name):
        return os.path.join(os.path.dirname(__file__), 'assets', name)

    @classmethod
    def fetch_card_back(cls, card_back, custom_card_back):
        if custom_card_back:
            return card_back

        if card_back in [1, 2, 3]:
            return cls.load_asset(f"{card_back}.png")

    @classmethod
    async def make_request(cls, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(str(url)) as response:
                return await response.read()

    @staticmethod
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

    async def add_gay(self, avatar_url: str, discord_file=True):
        """Adds gay overlay to image url given"""
        gay_image = PIL.Image.open(self.load_asset('gay.jpg'))
        background = PIL.Image.open(BytesIO(await self.make_request(avatar_url))).convert('RGBA')

        width, height = background.size
        foreground = gay_image.convert('RGBA').resize((width, height), PIL.Image.ANTIALIAS)

        return await self.merge_image(foreground, background, 0.4)

    async def merge_image(self, foreground, background, if_url: bool = False, blend_level: float = 0.6,
                          discord_file=True):
        """Merges two images together"""
        if if_url:
            foreground = PIL.Image.open(BytesIO(await self.make_request(foreground))).convert('RGBA')
            background = PIL.Image.open(BytesIO(await self.make_request(background))).convert('RGBA')
        result_bytes = BytesIO()
        width, height = background.size

        foreground = foreground.resize((width, height), PIL.Image.ANTIALIAS)
        result = PIL.Image.blend(background, foreground, alpha=blend_level)

        if discord_file:
            result.save(result_bytes, format="PNG")
            result_bytes.seek(0)
            return discord.File(result_bytes, filename="mergedimage.png")

        return result

    def create_card(self):
        img = PIL.Image.new('RGB', (900, 238), color=(91, 95, 102))

    async def create_profile(self, user: discord.Member, rank: int, level: int, xp: int, next_level_xp: int = None,
                             current_level_xp: int = None, discord_file=True):

        avatar = PIL.Image.open(BytesIO(await self.make_request(str(user.avatar_url))))
        avatar = avatar.convert('RGBA').resize((180, 180))
        card = Image.open(self.default_bg)
        card = card.resize((900, 238))
        font = ImageFont.truetype(self.font, 36)
        font_small = ImageFont.truetype(self.font, 20)
        result_bytes = BytesIO()

        status = Image.open(getattr(self, user.status.name))

        status = status.convert("RGBA").resize((55, 55))
        profile_pic_holder = Image.new("RGBA", card.size, (255, 255, 255, 0))

        mask = Image.new("RGBA", card.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse(
            (29, 29, 209, 209), fill=(255, 25, 255, 255)
        )

        draw = ImageDraw.Draw(card)
        draw.text((245, 60), f"{user}", self.txt_colour, font=font)
        draw.text((620, 60), f"Rank #{rank}", self.txt_colour, font=font)
        draw.text((245, 145), f"Level {level}", self.txt_colour, font=font_small)
        draw.text((620, 145), f"{self.human_format(xp)} / {self.human_format(next_level_xp)} XP", self.txt_colour,
                  font=font_small)

        blank = Image.new("RGBA", card.size, (255, 255, 255, 0))
        blankdraw = ImageDraw.Draw(blank)
        blankdraw.rounded_rectangle((245, 185, 750, 205), fill=(255, 255, 255, 0), outline=self.txt_colour, radius=10)

        xpneed = next_level_xp - current_level_xp
        xphave = xp - current_level_xp
        length_of_bar = (((xphave / xpneed) * 100) * 4.9) + 248

        blankdraw.rounded_rectangle((248, 188, length_of_bar, 202), fill=self.txt_colour, radius=7)

        profile_pic_holder.paste(avatar, (29, 29, 209, 209))
        precard = Image.composite(profile_pic_holder, card, mask)
        precard = precard.convert('RGBA')
        precard = Image.alpha_composite(precard, blank)

        blank = Image.new("RGBA", card.size, (255, 255, 255, 0))
        blank.paste(status, (155, 155))
        finalcard = Image.alpha_composite(precard, blank)

        if discord_file:
            finalcard.save(result_bytes, format="PNG")
            result_bytes.seek(0)
            return discord.File(result_bytes, filename="rankcard.png")

        return finalcard
