import discord
from discord.ext import commands
import aiohttp
from random import randint
from .utils.dataIO import dataIO
from cogs.utils import checks
import os

class giphy:
    """Show a gif using giphy"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/giphy/credentials.json"
        self.credentials = dataIO.load_json(self.file_path)

    @commands.command(pass_context=True)
    async def gif(self, ctx, *, query):
        """Shows a gif \n \n Put a number before your query to decide how much gifs you want to query (Defaults to 15)"""

        words = query.split(" ")

        if words[0].isdigit() == True:
            limit = words[0]
            if int(limit) > 100:
                limit = "100"
            query = " ".join(words[1:])
        else:
            limit = "15"

        # Query giphy search API
        async with aiohttp.get("http://api.giphy.com/v1/gifs/search?api_key=" + self.credentials['Apikey'] + "&q=" + query.replace(" ", "+") + "&limit=" + limit) as response:
            gif = await response.json()

        # Filter results to only show g, pg and pg-13 rated results
        filtered = [item for item in gif['data'] if item['rating'] in ("g", "pg", "pg-13")]

        # Count amount of results and shows one at random
        if len(filtered) == 0:
           await self.bot.say("No results.")
        else:
           mn = len(filtered)
           i = randint(0, mn-1)
           onegif = filtered[i]
           msg = "{} - {}".format(onegif['title'], onegif['url'])
           await self.bot.say(msg)

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def giphykey(self, ctx):
        """Set giphy api key"""
        await self.bot.whisper("Type your Apikey. You can reply in this private msg")
        username = await self.bot.wait_for_message(timeout=15, author=ctx.message.author)

        if username is None:
            return await self.bot.whisper("Apikey setup timed out.")

        else:
            self.credentials["Apikey"] = username.content
            dataIO.save_json(self.file_path, self.credentials)
            await self.bot.whisper("Setup complete. Apikey added.\nTry searching for "
                                   "a gif using {}gif".format(ctx.prefix))

def check_folders():
    if not os.path.exists("data/giphy"):
        print("Creating data/giphy folder...")
        os.makedirs("data/giphy")


def check_files():
    system = {"Apikey": ""}

    f = "data/giphy/credentials.json"
    if not dataIO.is_valid_json(f):
        print("Adding giphy credentials.json...")
        dataIO.save_json(f, system)

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(giphy(bot))
