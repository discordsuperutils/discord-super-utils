import PIL.ImageShow
import discord, PIL, os
import aiohttp  # koyashie fix unused / duplicate imports
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw


class ImageManager:
    def __init__(self, bot, txt_colour=None):
        self.bot = bot
        self.txt_colour = txt_colour  # choices: red, green , lime, cyan, blue, pink, yellow, purple
        self.default_bg = self.load_asset('card.jpg')
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
    async def make_request(cls, url):
        async with aiohttp.ClientSession as session:
            request = await session.get(url)
            return await request.read()

    async def add_gay(self, avatar_url: str, discord_file=True):
        """Adds gay overlay to image url given"""
        gay_image = PIL.Image.open(self.load_asset('gay.jpg'))
        background = PIL.Image.open(BytesIO(await self.make_request(avatar_url))).convert('RGBA')

        width, height = background.size
        foreground = gay_image.convert('RGBA').resize((width, height), PIL.Image.ANTIALIAS)

        return self.merge_image(foreground, background, 0.4)

    async def merge_image(self, foreground: PIL.Image, background: PIL.Image, blend_level: float = 0.6, discord_file=True):
        """Merges two images together"""
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

    async def create_profile(self, user: discord.Member, rank: int, level: int, xp: int, next_level_xp: int = None, current_level_xp: int = None, discord_file=True):

        avatar = PIL.Image.open(BytesIO(await self.make_request(user.avatar_url))).convert('RGBA').resize((180, 180))
        card = Image.open(self.default_bg)
        card = card.resize((900, 238))
        #bk = Image.open(self.bk).resize((850,210))
        font = ImageFont.truetype(self.font, 36)
        font_small = ImageFont.truetype(self.font, 20)
        #card.paste(bk, (23, 15))
        BLUE = (3, 78, 252)
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
        draw.text((245, 22), user.name, BLUE, font=font)
        draw.text((245, 80), f"Rank #{rank}", BLUE, font=font)
        draw.text((245, 123), f"Level {level}", BLUE, font=font_small)
        draw.text((245, 150),f"Exp {(xp)}/{(next_level_xp)}", BLUE, font=font_small)

        profile_pic_holder.paste(avatar, (29, 29, 209, 209))
        precard = Image.composite(profile_pic_holder, card, mask)
        precard = precard.convert('RGBA')

        blank = Image.new("RGBA", card.size, (255, 255, 255, 0))
        blank.paste(status, (165, 165))
        finalcard = Image.alpha_composite(precard, blank)

        if discord_file:
            finalcard.save(result_bytes, format="PNG")
            result_bytes.seek(0)
            return discord.File(result_bytes, filename="mergedimage.png")

        return finalcard
