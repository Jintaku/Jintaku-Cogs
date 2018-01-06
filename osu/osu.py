import discord
from discord.ext import commands
import aiohttp
from random import randint
from .utils.dataIO import dataIO
from cogs.utils import checks
import os

class osu:
    """Show stuff using osu!"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/osu/credentials.json"
        self.credentials = dataIO.load_json(self.file_path)

    @commands.command(pass_context=True)
    async def osu(self, ctx, *, query):
        """Shows a osu user!"""

        # Query osu! username API
        async with aiohttp.get("https://osu.ppy.sh/api/get_user?k=" + self.credentials['Apikey'] + "&u=" + query) as response:
            osu = await response.json()

        if osu:
           # Build Embed
           embed = discord.Embed()
           embed.title = osu[0]['username']
           embed.url = "https://osu.ppy.sh/u/{}".format(osu[0]['user_id'])
           embed.set_footer(text="Powered by osu!")
           embed.add_field(name="Accuracy", value=osu[0]['accuracy'][:4])
           embed.add_field(name="Level", value=osu[0]['level'][:5])
           embed.add_field(name="Ranked score", value=osu[0]['ranked_score'])
           embed.add_field(name="Rank", value=osu[0]['pp_rank'])
           embed.add_field(name="Country rank ({})".format(osu[0]['country']), value=osu[0]['pp_country_rank'])
           embed.add_field(name="Playcount", value=osu[0]['playcount'])
           await self.bot.say(embed=embed)
        else:
           await self.bot.say("No results.")


    @commands.command(pass_context=True)
    @checks.is_owner()
    async def osukey(self, ctx):
        """Set osu! api key"""
        await self.bot.whisper("Type your Apikey. You can reply in this private msg")
        username = await self.bot.wait_for_message(timeout=15, author=ctx.message.author)

        if username is None:
            return await self.bot.whisper("Apikey setup timed out.")

        else:
            self.credentials["Apikey"] = username.content
            dataIO.save_json(self.file_path, self.credentials)
            await self.bot.whisper("Setup complete. Apikey added.\nTry searching for "
                                   "a osu using {}osu".format(ctx.prefix))

def check_folders():
    if not os.path.exists("data/osu"):
        print("Creating data/osu folder...")
        os.makedirs("data/osu")


def check_files():
    system = {"Apikey": ""}

    f = "data/osu/credentials.json"
    if not dataIO.is_valid_json(f):
        print("Adding osu! credentials.json...")
        dataIO.save_json(f, system)

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(osu(bot))
