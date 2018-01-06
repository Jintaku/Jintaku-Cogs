import discord
from discord.ext import commands
import aiohttp
from random import randint
from .utils.dataIO import dataIO
from cogs.utils import checks
import os
import threading

class booru:
    """Show a picture using image boards (Gelbooru, yandere, konachan)"""

    def __init__(self, bot):
        self.bot = bot
        self.file_path = "data/booru/filters.json"
        self.filter_list = dataIO.load_json(self.file_path)

    @commands.command(pass_context=True)
    async def booru(self, ctx, rating, *, tag):
        """Shows a image board entry \n \n Ratings are : \n n: not filtered by rating \n e: explicit \n q: questionnable \n s: safe"""

        # Input handler and rating handler
        self.rating = rating
        global_filters = ["{}".format(self.filter_list['filter_list'])]
        tags = tag.split(" ")
        if global_filters != "":
           tags = global_filters + tags

           # Image board fetcher
           yan = threading.Thread(target=await self.fetch_yan(ctx, tags))
           gel = threading.Thread(target=await self.fetch_gel(ctx, tags))
           kon = threading.Thread(target=await self.fetch_kon(ctx, tags))
           dan = threading.Thread(target=await self.fetch_dan(ctx, tags))
           yan.join()
           gel.join()
           kon.join()
           dan.join()

           # Fuse multiple image board data
           data = self.yan_data + self.gel_data + self.kon_data + self.dan_data

           await self.booru_rating(ctx, data)

    async def fetch_from_booru(self, urlstr, provider): # Handles provider data and fetcher responses
       content = ""
       async with aiohttp.get(urlstr) as url:
           try:
               content = await url.json()
           except ValueError:
               content = None
       if not content or (type(content) is dict and 'success' in content.keys() and content['success'] == False):
           return []
       else:
         for item in content:
             item['provider'] = provider
       return content

    async def fetch_yan(self, ctx, tags): # Yande.re fetcher
        urlstr = "https://yande.re/post.json?limit=100&tags=" + "+".join(tags)
        self.yan_data = await self.fetch_from_booru(urlstr, "Yandere")

    async def fetch_gel(self, ctx, tags): # Gelbooru fetcher
        urlstr = "https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit=100&tags=" + "+".join(tags)
        self.gel_data = await self.fetch_from_booru(urlstr, "Gelbooru")

    async def fetch_kon(self, ctx, tags): # Konachan fetcher
        urlstr = "https://konachan.com/post.json?limit=100&tags=" + "+".join(tags)
        self.kon_data = await self.fetch_from_booru(urlstr, "Konachan")

    async def fetch_dan(self, ctx, tags): # Danbooru fetcher
        urlstr = "https://danbooru.donmai.us/posts.json?limit=100&tags=" + "+".join(tags[:2])
        self.dan_data = await self.fetch_from_booru(urlstr, "Danbooru")

    async def booru_rating(self, ctx, data): # Filters results based on rating input
           if self.rating in ("e", "s", "q"):
              filtered = [item for item in data if item['rating'] == self.rating]
              await self.show_booru(ctx, filtered)

           if self.rating == "n":
              filtered = data
              await self.show_booru(ctx, filtered)

           if self.rating not in ("n", "e", "s", "q"):
              await self.bot.say("Not valid rating")

    async def show_booru(self, ctx, filtered): #Shows various info in embed
       if len(filtered) == 0:
          await self.bot.say("No results.")
       else:
          # Chooses a random entry from the filtered data
          mn = len(filtered)
          i = randint(0, mn-1)
          onebooru = filtered[i]

          # Set variables for owner/author of post
          onebooru_author = onebooru.get('owner') or onebooru.get('author') or onebooru.get('uploader_name') or ''

          # Set variables for tags
          onebooru_tags = onebooru.get('tags') or onebooru.get('tag_string') or ''

          # Set variables for score
          onebooru_score = onebooru.get('score') or 'N/A'

          # Set variables for file url
          file_url = onebooru.get('file_url')
          if onebooru['provider'] == "Danbooru":
             file_url = "https://danbooru.donmai.us" + onebooru.get('file_url')
          onebooru_url = file_url

          # Build Embed
          embed = discord.Embed()
          embed.title = onebooru['provider'] + " entry by " + onebooru_author
          embed.url = onebooru_url
          embed.set_image(url=onebooru_url)
          embed.add_field(name="Tags", value=onebooru_tags, inline=False)
          embed.add_field(name="Rating", value=onebooru['rating'])
          embed.add_field(name="Score", value=onebooru_score)
          embed.set_footer(text="If image doesn't appear, it may be a webm or too big, Powered by {}".format(onebooru['provider']))
          await self.bot.say(embed=embed)

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def boorufilters(self, ctx):
        """Set image board tags as filters to be used on all requests"""
        if self.filter_list['filter_list'] == "":
           await self.bot.whisper("Type your filters all in one message")
           filter_list = await self.bot.wait_for_message(timeout=15, author=ctx.message.author)

           if filter_list is None:
               return await self.bot.whisper("Failed to add filters")

           else:
               self.filter_list["filter_list"] = filter_list.content.replace(" ", "+")
               dataIO.save_json(self.file_path, self.filter_list)
               await self.bot.whisper("Setup complete. filters added.\nTry searching "
                                      "using {}booru".format(ctx.prefix))
        else:
           await self.bot.whisper("Type your filters all in one message \n Your current list is `{}`".format(self.filter_list['filter_list'].replace("+", " ")))
           filter_list = await self.bot.wait_for_message(timeout=15, author=ctx.message.author)

           if filter_list is None:
               return await self.bot.whisper("Filters not modified")

           else:
               self.filter_list["filter_list"] = filter_list.content.replace(" ", "+")
               dataIO.save_json(self.file_path, self.filter_list)
               await self.bot.whisper("Setup complete. filters added.\nTry searching "
                                      "using {}booru".format(ctx.prefix))

def check_folders():
    if not os.path.exists("data/booru"):
        print("Creating data/booru folder...")
        os.makedirs("data/booru")


def check_files():
    system = {"filter_list": "rating:safe"}

    f = "data/booru/filters.json"
    if not dataIO.is_valid_json(f):
        print("Adding booru filters.json...")
        dataIO.save_json(f, system)

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(booru(bot))
