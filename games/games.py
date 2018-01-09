import discord
from discord.ext import commands
import aiohttp
from .utils.dataIO import dataIO
from cogs.utils import checks
import os
from datetime import datetime

class games:
    """Show stuff using games!"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/games/credentials.json"
        self.credentials = dataIO.load_json(self.file_path)

    @commands.command(pass_context=True)
    async def game(self, ctx, *, query):
        """Shows a games user!"""

        # Query IGDB API
        headers = {'user-key': self.credentials['Apikey'], 'Accept': 'application/json'}
        async with aiohttp.ClientSession() as session:
           async with session.get("https://api-2445582011268.apicast.io" + "/games/?search=" + query.replace(" ", "+") + "&fields=*", headers=headers) as response:
              games = await response.json()

        if games:
            totalResults = len(games)
            if totalResults == 1:
                entry = medias[0]
                await self.show_game(entry)
            elif totalResults > 1:
                medias = games
                msg = "**Please choose one by giving its number.**\n"
                for i in range(0, len(medias)):
                    release_date = medias[i].get('first_release_date')
                    if release_date:
                        release_date = datetime.fromtimestamp(release_date / 1000).strftime("%Y")
                    else:
                        release_date = "N/A"
                    msg += "\n{number} - {title} - {year}".format(number=i+1, title=medias[i]['name'], year=release_date)

                message = await self.bot.say(msg)

                check = lambda m: m.content.isdigit() and int(m.content) in range(1, len(medias) + 1)
                resp = await self.bot.wait_for_message(timeout=15, author=ctx.message.author,
                                                       check=check)

                # Delete messages to not pollute the chat
                await self.bot.delete_message(message)
                if resp:
                    await self.bot.delete_message(resp)
                else:
                    return

                entry = medias[int(resp.content)-1]
                await self.show_game(entry)
        else:
           await self.bot.say("No results.")

    async def show_game(self, entry):
        # Build Embed
        embed = discord.Embed()
        release_date = entry.get('first_release_date')
        if release_date:
            release_date = datetime.fromtimestamp(release_date / 1000).strftime("%Y")
        else:
            release_date = "N/A"
        embed.title = "{} {}".format(entry['name'], release_date)
        if entry['url']:
            embed.url = entry['url']
        if "summary" in entry.keys() and entry['summary']:
           embed.description = entry['summary'][:300] + "..."
        if 'cover' in entry.keys() and entry['cover']['url']:
           url = entry['cover']['url']
           if "http" not in url:
              url = "https:" + url
           embed.set_thumbnail(url=url)
        embed.set_footer(text="Powered by IGDB")

        await self.bot.say(embed=embed)


    @commands.command(pass_context=True)
    @checks.is_owner()
    async def IGDBkey(self, ctx):
        """Set IGDB api key"""
        await self.bot.whisper("Type your Apikey. You can reply in this private msg")
        username = await self.bot.wait_for_message(timeout=15, author=ctx.message.author)

        if username is None:
            return await self.bot.whisper("Apikey setup timed out.")

        else:
            self.credentials["Apikey"] = username.content
            dataIO.save_json(self.file_path, self.credentials)
            await self.bot.whisper("Setup complete. Apikey added.\nTry searching for "
                                   "a games using {}game".format(ctx.prefix))

def check_folders():
    if not os.path.exists("data/games"):
        print("Creating data/games folder...")
        os.makedirs("data/games")


def check_files():
    system = {"Apikey": ""}

    f = "data/games/credentials.json"
    if not dataIO.is_valid_json(f):
        print("Adding games! credentials.json...")
        dataIO.save_json(f, system)

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(games(bot))
