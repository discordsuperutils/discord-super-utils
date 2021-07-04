import PIL.ImageShow
import discord, PIL, requests, os
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw


class ImageManager:
    def __init__(self, bot, txt_colour = None):
        self.bot = bot
        self.txt_colour = txt_colour #choices: red, green , lime, cyan, blue, pink, yellow, purple,
        self.default_bg = os.path.join(os.path.dirname(__file__), 'assets', 'card.jpg')
        self.online = os.path.join(os.path.dirname(__file__), 'assets', 'online.png')
        self.offline = os.path.join(os.path.dirname(__file__), 'assets', 'offline.png')
        self.idle = os.path.join(os.path.dirname(__file__), 'assets', 'idle.png')
        self.dnd = os.path.join(os.path.dirname(__file__), 'assets', 'dnd.png')
        self.streaming = os.path.join(os.path.dirname(__file__), 'assets', 'streaming.png')
        self.font = os.path.join(os.path.dirname(__file__), 'assets', 'font.ttf')
        self.bk = os.path.join(os.path.dirname(__file__), 'assets', 'grey.png')

    def add_gay(self, avatar_url: str, discord_file=True):
        """Adds gay overlay to image url given"""
        b = BytesIO()
        f = os.path.join(os.path.dirname(__file__), 'assets', 'gay.jpg')
        data = requests.get(avatar_url)
        av = PIL.Image.open(BytesIO(data.content))
        gayimg = PIL.Image.open(f)

        background = av.convert('RGBA')
        foreground = gayimg.convert('RGBA')
        width, height = background.size

        foreground = foreground.resize((width, height), PIL.Image.ANTIALIAS)
        avatar = PIL.Image.blend(background, foreground, alpha=0.4)

        if discord_file:
            avatar.save(b, format="PNG")
            b.seek(0)
            return discord.File(b, filename="rank.png")

        return avatar

    def merge_image(self, foreground: str, background : str , blend_level : float = 0.6,  discord_file=True):
        """Merges two images together"""
        b = BytesIO()
        fg = requests.get(foreground)
        foreground = PIL.Image.open(BytesIO(fg.content))
        bg = requests.get(background)
        background = PIL.Image.open(BytesIO(bg.content))

        background = background.convert('RGBA')
        foreground = foreground.convert('RGBA')
        width, height = background.size

        foreground = foreground.resize((width, height), PIL.Image.ANTIALIAS)
        avatar = PIL.Image.blend(background, foreground, alpha= blend_level)

        if discord_file:
            avatar.save(b, format="PNG")
            b.seek(0)
            return discord.File(b, filename="mergedimage.png")

        return avatar

    def create_card(self):
        img = PIL.Image.new('RGB', (900, 238), color = (91, 95, 102))

    def create_profile(self, user : discord.Member, rank : int, level : int, xp : int, next_level_xp : int = None, current_level_xp : int = None, discord_file=True):

        avatar = (PIL.Image.open(BytesIO(requests.get(user.avatar_url).content))).convert('RGBA').resize((180, 180))
        test = current_level_xp
        card = Image.open(self.default_bg)
        card = card.resize((900, 238))
        #bk = Image.open(self.bk).resize((850,210))
        font = ImageFont.truetype(self.font, 36)
        font_small = ImageFont.truetype(self.font, 20)
        #card.paste(bk, (23, 15))
        BLUE = (3, 78, 252)
        b = BytesIO()

        if user.status.name == 'online':
            status = Image.open(self.online)
        if user.status.name == 'offline':
            status = Image.open(self.offline)
        if user.status.name == 'idle':
            status = Image.open(self.idle)
        if user.status.name == 'streaming':
            status = Image.open(self.streaming)
        if user.status.name == 'dnd':
            status = Image.open(self.dnd)

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
            finalcard.save(b, format="PNG")
            b.seek(0)
            return discord.File(b, filename="mergedimage.png")
        return finalcard