import discord
from discord.ext import commands
import requests
from random import randint

class xkcd:
    """Search wikia"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def xkcd(self, ctx):
        """Post a random xkcd"""

        # Creates random number between 0 and 1935 (number of xkcd comics at time of writing) and queries xkcd
        i = randint(0, 1935)
        response = requests.get("https://xkcd.com/" + str(i) + "/info.0.json")
        xkcd = response.json()

        # Build Embed
        embed = discord.Embed()
        embed.title = xkcd['title'] + " (" + xkcd['day'] + "/" + xkcd['month'] + "/" + xkcd['year'] + ")"
        embed.url = "https://xkcd.com/" + str(i)
        embed.description = xkcd['alt']
        embed.set_image(url=xkcd['img'])
        embed.set_footer(text="Powered by xkcd")
        await self.bot.say(embed=embed)

def setup(bot):
    bot.add_cog(xkcd(bot))
