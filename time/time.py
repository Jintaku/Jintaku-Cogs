import discord
from discord.ext import commands
import aiohttp

class time:
    """Shows time"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def time(self, ctx, *, title):
        """Shows what time it is in other places"""

        # Queries timezoneapi
        async with aiohttp.get("https://timezoneapi.io/api/address/?{}".format(title)) as response:
            data = await response.json()
            
        # Set up variables for Embed
        if data['data']['addresses_found'] != "0":
           City = data['data']['addresses'][0]['formatted_address']
           Time = data['data']['addresses'][0]['datetime']['date_time_txt']
           Execution_Time = data['meta']['execution_time']

           # Build Embed
           embed = discord.Embed()
           embed.title = City
           embed.description = Time
           embed.set_footer(text="Powered by Timezoneapi.io in {}".format(Execution_Time))
           await self.bot.say(embed=embed)

        if data['data']['addresses_found'] == "0":
           self.bot.say("No result")


def setup(bot):
    bot.add_cog(time(bot))
