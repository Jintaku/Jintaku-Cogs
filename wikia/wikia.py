import discord
from discord.ext import commands
import aiohttp

class wikia:
    """Search wikia"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def wikia(self, ctx, *, subdomain):
        """Search wikia subdomain then bot will ask you which article you want to consult"""

        # the command starts by searching the subdomain the user entered
        subdomains = await self.search_wikiadomains(subdomain)

        # Verify how many subdomains the search returned.
        # if there is more than one domain, the user will be prompted 
        # to select which one to use before continuing
        wikia_domain = ""
        if len(subdomains) == 0:
            await self.bot.say("No subdomain found. Aborting.")
            return
        elif len(subdomains) == 1:
            wikia_domain = subdomains[0]['domain']
        else:
            data = ["{number} - {title} - ({subdomain})".format(number=i+1, title=subdomains[i]['name'], subdomain=subdomains[i]['domain']) for i in range(0, len(subdomains))]
            msg = "\n".join(["Multiple results found. Pick one:",] + data)
            message = await self.bot.say(msg)
            check = lambda m: m.content.isdigit() and int(m.content) in range(1, len(subdomains) + 1)
            resp = await self.bot.wait_for_message(timeout=15, author=ctx.message.author, check=check)

            # Deletes messages to not pollute the chat
            await self.bot.delete_message(message)
            if resp:
                await self.bot.delete_message(resp)
            else:
                await self.bot.say("Too late")
                return
            entry = subdomains[int(resp.content)-1]
            wikia_domain = entry['domain']

        message = await self.bot.say("Enter the wikia article for domain " + wikia_domain + ":")
        resp = await self.bot.wait_for_message(timeout=15, author=ctx.message.author)

        # Deletes messages to not pollute the chat
        await self.bot.delete_message(message)
        if resp:
            await self.bot.delete_message(resp)
        else:
            await self.bot.say("Too late")
            return
        await self.wikiasearch(ctx, wikia_domain.split(".")[0], resp.content)

    async def wikiasearch(self, ctx, wikia_domain, wikia_entry):
        """Receives a wikia domain and a searched article.
        Will search articles for the selected domain and prompt the user if more than one is found.
        Selected article will be shown to the user.
        """

        query_string = wikia_entry.replace(' ', '+')
        data = None

        # Queries api to search an article
        async with aiohttp.get("http://" + str(wikia_domain) + ".wikia.com/api/v1/Search/List/?query=" + query_string + "&namespaces=0%2C14&limit=10") as response:
            data = await response.json()

        if not 'items' in data.keys() or len(data['items']) == 0:
           await self.bot.say("No results")
        else:
            if len(data['items']) == 1:
               entry = data['items'][0]
               wikia_id = entry['id']
               await self.show_wikia(wikia_id)
            else:
               medias = data['items']
               msg = "**Please choose one by giving its number.**\n"
               for i in range(0, len(medias)):
                   msg += "\n{number} - {title}".format(number=i+1, title=medias[i]['title'])

               message = await self.bot.say(msg)

               check = lambda m: m.content.isdigit() and int(m.content) in range(1, len(medias) + 1)
               resp = await self.bot.wait_for_message(timeout=15, author=ctx.message.author,
                                                        check=check)

               # Deletes messages to not pollute the chat
               await self.bot.delete_message(message)
               if resp:
                   await self.bot.delete_message(resp)
               else:
                   return

               entry = medias[int(resp.content)-1]
               wikia_id = entry['id']
               await self.show_wikia(wikia_domain, wikia_id)

    async def show_wikia(self, wikia_domain, wikia_id):
        """Receive the wikia domain and the id of the article to display
        Will build a discord embed and show it in the channel"""

        data = None

        # Queries api to get information about article
        async with aiohttp.get("http://" + str(wikia_domain) + ".wikia.com/api/v1/Articles/Details/?ids=" + str(wikia_id) + "&abstract=100&width=200&height=200") as response:
            data = await response.json()

        selected_wikia = data['items'][str(wikia_id)]

        # Build Embed
        embed = discord.Embed()
        embed.title = selected_wikia['title']
        embed.url = "http://{}.wikia.com{}".format(wikia_domain, selected_wikia['url'])
        if selected_wikia['thumbnail'] is not None:
           embed.set_thumbnail(url=selected_wikia['thumbnail'])
        if selected_wikia['abstract'] != "":
           embed.description = selected_wikia['abstract']
        embed.set_footer(text="Powered by wikia")
        await self.bot.say(embed=embed)

    async def search_wikiadomains(self, subdomain_entry):
        """Receive a search query for a subdomain from the user
        Will search subdomains matching the query and return results in an array"""
        query_string = subdomain_entry.replace(' ', '+')

        # Queries api to search wikia subdomains
        async with aiohttp.get("http://www.wikia.com/api/v1/Wikis/ByString/?string=" + query_string + "&limit=10&batch=1&lang=en") as response:
            data = await response.json()
            return data['items']


def setup(bot):
    bot.add_cog(wikia(bot))
