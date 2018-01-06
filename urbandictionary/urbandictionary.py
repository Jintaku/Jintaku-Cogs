import discord
from discord.ext import commands
import aiohttp
from random import randint

class urbandictionary:
    """Search urban dictionary"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def ud(self, ctx, *, word):
        """Post a urban dictionary entry"""

        word_entry = word.replace(" ", "+")

        # Queries unofficial urbandictionary API
        async with aiohttp.get("http://api.urbandictionary.com/v0/define?term=" + str(word_entry).lower()) as response:
            ud = await response.json()

        # Counts results and shows a random entry
        if ud['result_type'] != "exact":
           await self.bot.say("No results")
        else:
           n = len(ud['list'])
           mn = n-1
           i = randint(0, mn)
           oneud = ud['list'][i]

           # Build Embed
           embed = discord.Embed()
           embed.title = oneud['word'].capitalize() + " by " + oneud['author']
           embed.url = oneud['permalink']
           embed.description = oneud['definition'] + "\n \n **Example : **" + oneud.get('example', "N/A")
           embed.set_footer(text=str(oneud['thumbs_down']) + " Down / " + str(oneud['thumbs_up']) + " Up , Powered by urban dictionary")
           await self.bot.say(embed=embed)

def setup(bot):
    bot.add_cog(urbandictionary(bot))
