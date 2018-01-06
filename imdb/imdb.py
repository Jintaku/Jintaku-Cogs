import discord
from discord.ext import commands
import aiohttp
from .utils.dataIO import dataIO
from cogs.utils import checks
import os

class Imdb:
    """Shows movie info"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/imdb/credentials.json"
        self.credentials = dataIO.load_json(self.file_path)

    @commands.command(pass_context=True)
    async def movie(self, ctx, title):
        """Search a movie"""

        titlesearch = title.replace(' ', '_')

        # Query omdb api for movie results
        async with aiohttp.get("http://www.omdbapi.com/?apikey=" + self.credentials["Apikey"] + "&s=" + titlesearch + "&plot=short") as response:
            data = await response.json()

        # Handle response based on query result and user input
        if data['Response'] == "False":
            await self.bot.say("I couldn't find anything!")
        if data['Response'] == "True":
            if data['totalResults'] == "1":
                await self.show_movie(data['Search'][0]['imdbID'])
            if data['totalResults'] != "1":
                medias = data['Search']
                msg = "**Please choose one by giving its number.**\n"
                for i in range(0, len(medias)):
                    msg += "\n{number} - {title} - {year}".format(number=i+1, title=medias[i]['Title'], year=medias[i]['Year'])

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
                await self.show_movie(entry['imdbID'])

    async def show_movie(self, imdbID):
        """Show a movie"""

        # Queries omdb api for movie information
        async with aiohttp.get("http://www.omdbapi.com/?apikey=" + self.credentials["Apikey"] + "&i=" + imdbID + "&plot=full") as response:
            data = await response.json()

        # Build Embed
        embed = discord.Embed()
        embed.title = "{} {}".format(data['Title'], data['Year'])
        if data['imdbID']:
           embed.url = "http://www.imdb.com/title/{}".format(data['imdbID'])
        if data['Plot']:
           embed.description = data['Plot']
        if data['Poster'] != "N/A":
           embed.set_thumbnail(url=data['Poster'])
        if data['Runtime']:
           embed.add_field(name="Runtime", value=data.get('Runtime', 'N/A'))
        if data['Genre']:
           embed.add_field(name="Genre", value=data.get('Genre', 'N/A'))
        if data.get("BoxOffice"):
           embed.add_field(name="Box Office", value=data.get('BoxOffice', 'N/A'))
        if data['Metascore']:
           embed.add_field(name="Metascore", value=data.get('Metascore', 'N/A'))
        embed.set_footer(text="Powered by omdb")
        await self.bot.say(embed=embed)

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def omdbkey(self, ctx): # Set omdb api api_key
        """Set omdb api key in private messages"""
        await self.bot.whisper("Type your Apikey. You can reply in this private msg")
        username = await self.bot.wait_for_message(timeout=15, author=ctx.message.author)

        if username is None:
            return await self.bot.whisper("Apikey setup timed out.")

        else:
            self.credentials["Apikey"] = username.content
            dataIO.save_json(self.file_path, self.credentials)
            await self.bot.whisper("Setup complete. Apikey added.\nTry searching for "
                                   "a movie using {}movie".format(ctx.prefix))

def check_folders():
    if not os.path.exists("data/imdb"):
        print("Creating data/imdb folder...")
        os.makedirs("data/imdb")


def check_files():
    system = {"Apikey": ""}

    f = "data/imdb/credentials.json"
    if not dataIO.is_valid_json(f):
        print("Adding imdb credentials.json...")
        dataIO.save_json(f, system)

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Imdb(bot))
