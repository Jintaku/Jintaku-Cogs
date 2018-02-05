from urllib.parse import quote
import discord
from discord.ext import commands
import aiohttp
from .utils.dataIO import dataIO
from datetime import datetime
from cogs.utils import checks
import os


numbs = {
    "next": "➡",
    "back": "⬅",
    "exit": "❌"
}


class games:
    """Search games using IGDB"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/games/credentials.json"
        self.credentials = dataIO.load_json(self.file_path)

    async def _search_games(self, ctx, url):
        # future response dict
        data = None

        try:
            headers = {'user-key': self.credentials['Apikey'], 'Accept': 'application/json'}
            async with aiohttp.get(url, headers=headers) as response:
                data = await response.json()

        except:
            return None

        if data is not None and len(data) > 0:

            # a list of embeds
            embeds = []

            for games in data:
                release_date = games.get('first_release_date')
                if release_date:
                    release_date = datetime.fromtimestamp(release_date / 1000).strftime("%Y")
                else:
                    release_date = "N/A"
                if 'cover' in games.keys() and games['cover']['url']:
                   url = games['cover']['url']
                   if "http" not in url:
                      url = "https:" + url
                embed = discord.Embed(title="{} {}".format(games['name'], release_date),
                                      url=games['url'],
                                      description=games.get('summary', 'N/A')[:300] + "...")
                embed.set_thumbnail(url=url)
                embed.set_footer(text="Powered by IGDB")
                embeds.append(embed)

            return embeds, data

        else:
            return None

    @commands.command(pass_context=True)
    async def game(self, ctx, *, query):
        """Searches for game information using IGDB"""

        try:
            # URL for IGDB api
            url = "https://api-2445582011268.apicast.io/games/?search=" + query.replace(" ", "+") + "&fields=*"

            embeds, data = await self._search_games(ctx, url)

            if embeds is not None:
                await self.game_menu(ctx, embeds, message=None, page=0, timeout=30, edata=data)
            else:
                await self.bot.say('No games were found or there was an error in the process')

        except TypeError:
            await self.bot.say('No games were found or there was an error in the process')

    async def game_menu(self, ctx, cog_list: list,
                        message: discord.Message=None,
                        page=0, timeout: int=30, edata=None):
        """menu control logic for this taken from
           https://github.com/Lunar-Dust/Dusty-Cogs/blob/master/menu/menu.py"""
        cog = cog_list[page]

        expected = ["➡", "⬅", "❌"]

        if not message:
            message =\
                await self.bot.send_message(ctx.message.channel, embed=cog)
            await self.bot.add_reaction(message, "⬅")
            await self.bot.add_reaction(message, "❌")
            await self.bot.add_reaction(message, "➡")
        else:
            message = await self.bot.edit_message(message, embed=cog)
        react = await self.bot.wait_for_reaction(
            message=message, user=ctx.message.author, timeout=timeout,
            emoji=expected
        )
        if react is None:
            try:
                try:
                    await self.bot.clear_reactions(message)
                except:
                    await self.bot.remove_reaction(message, "⬅", self.bot.user)
                    await self.bot.remove_reaction(message, "❌", self.bot.user)
                    await self.bot.remove_reaction(message, "➡", self.bot.user)
            except:
                pass
            return None
        reacts = {v: k for k, v in numbs.items()}
        react = reacts[react.reaction.emoji]
        if react == "next":
            page += 1
            next_page = page % len(cog_list)
            try:
                await self.bot.remove_reaction(message, "➡", ctx.message.author)
            except:
                pass
            return await self.game_menu(ctx, cog_list, message=message,
                                        page=next_page, timeout=timeout, edata=edata)
        elif react == "back":
            page -= 1
            next_page = page % len(cog_list)
            try:
                await self.bot.remove_reaction(message, "⬅", ctx.message.author)
            except:
                pass
            return await self.game_menu(ctx, cog_list, message=message,
                                        page=next_page, timeout=timeout, edata=edata)

        else:
            try:
                return await self.bot.delete_message(message)
            except:
                pass

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
