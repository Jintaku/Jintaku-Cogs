import discord
from discord.ext import commands
import aiohttp


numbs = {
    "next": "➡",
    "back": "⬅",
    "exit": "❌"
}


class urbandictionary:
    """Search games using IGDB"""

    def __init__(self, bot):
        self.bot = bot

    async def _search_ud(self, ctx, url):
        # future response dict
        data = None

        try:
            async with aiohttp.get(url) as response:
                data = await response.json()

        except:
            return None

        if data is not None and len(data) > 0:

            # a list of embeds
            embeds = []
            print(data)
            for ud in data['list']:
                embed = discord.Embed()
                embed.title = ud['word'].capitalize() + " by " + ud['author']
                embed.url = ud['permalink']
                embed.description = ud['definition'] + "\n \n **Example : **" + ud.get('example', "N/A")
                embed.set_footer(text=str(ud['thumbs_down']) + " Down / " + str(ud['thumbs_up']) + " Up , Powered by urban dictionary")
                embeds.append(embed)

            return embeds, data

        else:
            return None

    @commands.command(pass_context=True)
    async def ud(self, ctx, *, word):
        """Searches for game information using IGDB"""

        try:
            # URL for IGDB api
            url = "http://api.urbandictionary.com/v0/define?term=" + str(word).lower()

            embeds, data = await self._search_ud(ctx, url)

            if embeds is not None:
                await self.game_menu(ctx, embeds, message=None, page=0, timeout=30, edata=data)
            else:
                await self.bot.say('No Urban dictionary were found or there was an error in the process')

        except TypeError:
            await self.bot.say('No Urban dictionary were found or there was an error in the process')

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

def setup(bot):
   bot.add_cog(urbandictionary(bot))
