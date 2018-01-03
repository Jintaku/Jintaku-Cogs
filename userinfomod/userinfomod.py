#  Modified by Lionirdeadman to fuse userinfo (https://github.com/Cog-Creators/Red-DiscordBot) and imgwelcome (https://github.com/aikaterna/aikaterna-cogs/)
# Tried to document and understand more but not a success

import asyncio
import aiohttp
import datetime
import discord
import os
import re
import time
from __main__ import send_cmd_help
from cogs.utils.dataIO import dataIO
from cogs.utils import checks
from copy import deepcopy
from discord.ext import commands
from io import BytesIO
from PIL import Image, ImageFont, ImageOps, ImageDraw


default_settings = {"BACKGROUND": "data/userinfomod/transparent.png",
                    "BORDER": [255, 255, 255, 230],
                    "CHANNEL": None,
                    "OUTLINE": [0, 0, 0, 255],
                    "SERVERTEXT": [255, 255, 255, 230],
                    "TEXT": [255, 255, 255, 230],
                    "FONT": {"USER_FONT": {"PATH": "data/userinfomod/fonts/UniSansHeavy.otf",
                                               "SIZE": 50},
                             "SERVER_FONT": {"PATH": "data/userinfomod/fonts/UniSansHeavy.otf",
                                              "SIZE": 20},
                             "NAME_FONT": {"PATH": "data/userinfomod/fonts/UniSansHeavy.otf",
                                            "SIZE": {"NORMAL": 30,
                                                      "MEDIUM": 22,
                                                      "SMALL": 18,
                                                      "SMALLEST": 12
                                                    }
                                            }
                            }
                    }


class userinfomod:
    """Displays user info as image."""

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json('data/userinfomod/settings.json')
        self.version = "1"

    async def save_settings(self):
        dataIO.save_json('data/userinfomod/settings.json', self.settings)

    async def _create_user(self, member, url, test_member_number: int = None):
        server = member.server
        wfont = self.settings[server.id]["FONT"]["USER_FONT"]
        sfont = self.settings[server.id]["FONT"]["SERVER_FONT"]
        nfont = self.settings[server.id]["FONT"]["NAME_FONT"]
        user_font = ImageFont.truetype(wfont["PATH"], wfont["SIZE"])
        server_font = ImageFont.truetype(sfont["PATH"], sfont["SIZE"])

        name_font = ImageFont.truetype(nfont["PATH"], nfont["SIZE"]["NORMAL"])
        name_font_medium = ImageFont.truetype(nfont["PATH"], nfont["SIZE"]["MEDIUM"])
        name_font_small = ImageFont.truetype(nfont["PATH"], nfont["SIZE"]["SMALL"])
        name_font_smallest = ImageFont.truetype(nfont["PATH"], nfont["SIZE"]["SMALLEST"])
        background = Image.open(self.settings[server.id]["BACKGROUND"]).convert('RGBA')
        no_profile_picture = Image.open("data/userinfomod/noimage.png")

        global user_picture
        user_picture = Image.new("RGBA", (500, 150))
        user_picture = ImageOps.fit(background, (500, 150), centering=(0.5, 0.5))
        user_picture.paste(background)
        user_picture = user_picture.resize((500, 150), Image.NEAREST)

        profile_area = Image.new("L", (512, 512), 0)
        draw = ImageDraw.Draw(profile_area)
        draw.ellipse(((0, 0), (512, 512)), fill=255)
        circle_img_size = tuple(self.settings[member.server.id]["CIRCLE"])
        profile_area = profile_area.resize((circle_img_size), Image.ANTIALIAS)
        try:
            url = url.replace('webp?size=1024', 'png')
            url = url.replace('gif?size=1024', 'png')
            await self._get_profile(url)
            profile_picture = Image.open('data/userinfomod/profilepic.png')
        except:
            profile_picture = no_profile_picture
        profile_area_output = ImageOps.fit(profile_picture, (circle_img_size), centering=(0, 0))
        profile_area_output.putalpha(profile_area)

        bordercolor = tuple(self.settings[member.server.id]["BORDER"])
        fontcolor = tuple(self.settings[member.server.id]["TEXT"])
        servercolor = tuple(self.settings[member.server.id]["SERVERTEXT"])
        textoutline = tuple(self.settings[server.id]["OUTLINE"])

        mask = Image.new('L', (512, 512), 0)
        draw_thumb = ImageDraw.Draw(mask)
        draw_thumb.ellipse((0, 0) + (512, 512), fill=255, outline=0)
        circle = Image.new("RGBA", (512, 512))
        draw_circle = ImageDraw.Draw(circle)
        draw_circle.ellipse([0, 0, 512, 512], fill=(bordercolor[0], bordercolor[1], bordercolor[2], 180), outline=(255, 255, 255, 250))
        circle_border_size = await self._circle_border(circle_img_size)
        circle = circle.resize((circle_border_size), Image.ANTIALIAS)
        circle_mask = mask.resize((circle_border_size), Image.ANTIALIAS)
        circle_pos = (7 + int((136 - circle_border_size[0]) / 2))
        border_pos = (11 + int((136 - circle_border_size[0]) / 2))
        drawtwo = ImageDraw.Draw(user_picture)
        user_picture.paste(circle, (circle_pos, circle_pos), circle_mask)
        user_picture.paste(profile_area_output, (border_pos, border_pos), profile_area_output)

        uname = (str(member.name) + "#" + str(member.discriminator))

        def _outline(original_position: tuple, text: str, pixel_displacement: int, font, textoutline):

            op = original_position
            pd = pixel_displacement

            left = (op[0] - pd, op[1])
            right = (op[0] + pd, op[1])
            up = (op[0], op[1] - pd)
            down = (op[0], op[1] + pd)

            drawtwo.text(left, text, font=font, fill=(textoutline))
            drawtwo.text(right, text, font=font, fill=(textoutline))
            drawtwo.text(up, text, font=font, fill=(textoutline))
            drawtwo.text(down, text, font=font, fill=(textoutline))

            drawtwo.text(op, text, font=font, fill=(textoutline))

        _outline((150, 16), "User info", 1, user_font, (textoutline))
        drawtwo.text((150, 16), "User info", font=user_font, fill=(fontcolor))

        if len(uname) <= 17:
            _outline((152, 63), uname, 1, name_font, (textoutline))
            drawtwo.text((152, 63), uname, font=name_font, fill=(fontcolor))

        if len(uname) > 17:
            if len(uname) <= 23:
                _outline((152, 66), uname, 1,  name_font_medium, (textoutline))
                drawtwo.text((152, 66), uname, font=name_font_medium, fill=(fontcolor))

        if len(uname) >= 24:
            if len(uname) <= 32:
                _outline((152, 70), uname, 1,  name_font_small, (textoutline))
                drawtwo.text((152, 70), uname, font=name_font_small, fill=(fontcolor))

        if len(uname) >= 33:
            drawtwo.text((152, 73), uname, 1,  name_font_smallest, (textoutline))
            drawtwo.text((152, 73), uname, font=name_font_smallest, fill=(fontcolor))

        if test_member_number is None:
            members = sorted(server.members,
                               key=lambda m: m.joined_at).index(member) + 1
        else:
            members = test_member_number

        # Set up variables for font creation
        date_join = datetime.datetime.strptime(str(member.joined_at), "%Y-%m-%d %H:%M:%S.%f")
        date_now = datetime.datetime.now(datetime.timezone.utc)
        date_now = date_now.replace(tzinfo=None)
        since_join = date_now - date_join
        member_number = str(members) + self._get_suffix(members)

        # Create outline and text
        _outline((152, 96), str(member_number) + " member", 1, server_font, (textoutline))
        drawtwo.text((152, 96), str(member_number) + " member", font=server_font, fill=(servercolor))
        _outline((152, 116), "Here since " + str(since_join.days) + "days ago!", 1, server_font, (textoutline))
        drawtwo.text((152, 116), "Here since " + str(since_join.days) + "days ago!", font=server_font, fill=(servercolor))

        image_object = BytesIO()
        user_picture.save(image_object, format="PNG")
        image_object.seek(0)
        return image_object

    async def _circle_border(self, circle_img_size: tuple):
        border_size = []
        for i in range(len(circle_img_size)):
            border_size.append(circle_img_size[0] + 8)
        return tuple(border_size)

    async def _data_check(self, ctx): # Check if data and configs are there
        server = ctx.message.server
        if server.id not in self.settings:
            self.settings[server.id] = deepcopy(default_settings)
            self.settings[server.id]["CHANNEL"] = ctx.message.channel.id
            await self.save_settings()

        if "CIRCLE" not in self.settings[server.id].keys():
            self.settings[server.id]["CIRCLE"] = [128, 128]
            await self.save_settings()

        if "CHANNEL" not in self.settings[server.id].keys():
            self.settings[server.id]["CHANNEL"] = ctx.message.channel.id
            await self.save_settings()

        if "FONT" not in self.settings[server.id].keys():
            self.settings[server.id]["FONT"] = {"USER_FONT": {"PATH": "data/userinfomod/fonts/UniSansHeavy.otf",
                                                                  "SIZE": 50},
                                                "SERVER_FONT": {"PATH": "data/userinfomod/fonts/UniSansHeavy.otf",
                                                                 "SIZE": 20},
                                                "NAME_FONT": {"PATH": "data/userinfomod/fonts/UniSansHeavy.otf",
                                                               "SIZE": {"NORMAL": 30,
                                                                         "MEDIUM": 22,
                                                                         "SMALL": 18,
                                                                         "SMALLEST": 12
                                                                        }
                                                                }
                                                }

        if "OUTLINE" not in self.settings[server.id].keys():
            self.settings[server.id]["OUTLINE"] = [0, 0, 0, 255]
            await self.save_settings()

    async def _get_profile(self, url):
        async with aiohttp.get(url) as r:
            image = await r.content.read()
        with open('data/userinfomod/profilepic.png', 'wb') as f:
            f.write(image)

    def _get_suffix(self, num):
        suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
        if 10 <= num % 100 <= 20:
            suffix = 'th'
        else:
            suffix = suffixes.get(num % 10, 'th')
        return suffix

    def _hex_to_rgb(self, hex_num: str, a: int):
        h = hex_num.lstrip('#')

        # if only 3 characters are given
        if len(str(h)) == 3:
            expand = ''.join([x*2 for x in str(h)])
            h = expand

        colors = [int(h[i:i+2], 16) for i in (0, 2, 4)]
        colors.append(a)
        return tuple(colors)

    def _is_hex(self, color: str):
        if color is not None and len(color) != 4 and len(color) != 7:
            return False

        reg_ex = r'^#(?:[0-9a-fA-F]{3}){1,2}$'
        return re.search(reg_ex, str(color))

    def _rgb_to_hex(self, rgb):
        rgb = tuple(rgb[:3])
        return '#%02x%02x%02x' % rgb

    @commands.command(pass_context=True, no_pm=True)
    async def uinfo(self, ctx, *, member: discord.Member=None, number: int=None):
        """Shows users's informations"""

        #Set up variables to create image
        author = ctx.message.author
        server = ctx.message.server
        channel = ctx.message.channel

        #Sends info and various things to create image
        if not member:
            member = author
        await self._data_check(ctx)
        channel_object = self.bot.get_channel(channel.id)
        await self.bot.send_typing(channel_object)
        image_object = await self._create_user(member, member.avatar_url, number)
        await self.bot.send_file(channel_object, image_object, filename="userinfo.png")


def check_folders():
    if not os.path.exists('data/userinfomod/'):
        os.mkdir('data/userinfomod/')


def check_files():
    if not dataIO.is_valid_json('data/userinfomod/settings.json'):
        defaults = {}
        dataIO.save_json('data/userinfomod/settings.json', defaults)


def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(userinfomod(bot))
