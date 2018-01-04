# Original credit and design goes to mee6 and Redjumpman
# Modified by Lionirdeadman and Ben (Mostly Ben. He's hella gud)
import os
import re
import discord
from discord.ext import commands
import requests
import datetime


class AniSearch:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, no_pm=True)
    async def anime(self, ctx, *, title):
        """Shows AniList information on an anime"""
        cmd = "ANIME"
        await self.fetch_info_anime_manga(ctx, cmd, title)

    @commands.command(pass_context=True, no_pm=True)
    async def manga(self, ctx, *, title):
        """Shows AniList information on a manga"""
        cmd = "MANGA"
        await self.fetch_info_anime_manga(ctx, cmd, title)

    @commands.command(pass_context=True, no_pm=True)
    async def user(self, ctx, *, username):
        """Shows AniList information on a user"""
        await self.fetch_info_user(ctx, username)

    @commands.command(pass_context=True, no_pm=True)
    async def character(self, ctx, *, name):
        """Shows AniList information on a character"""
        await self.fetch_info_character(ctx, name)

    def format_name(self, first_name, last_name): # Combines first_name and last_name and/or shows either of the two
      if first_name and last_name:
          return first_name + " " + last_name
      elif first_name:
          return first_name
      elif last_name:
          return last_name
      else:
          return 'No name'

    def clean_html(self, description): # Removes html tags
      if not description:
          return ""
      cleanr = re.compile("<.*?>")
      cleantext = re.sub(cleanr, "", description)
      return cleantext

    def clean_spoilers(self, description): # Removes spoilers using the html tag given by AniList
      if not description:
          return ""
      cleanr = re.compile("/<span[^>]*>.*<\/span>/g")
      cleantext = re.sub(cleanr, "", description)
      return cleantext

    def description_parser(self, description): # Limits text to 400characters and 5 lines and adds "..." at the end
        description = self.clean_spoilers(description)
        description = self.clean_html(description)
        description = "\n".join(description.split("\n")[:5])
        if len(description) > 400:
            return description[:400] + "..."
        else:
            return description

    def list_maximum(self, items): # Limits to 5 strings than adds "+X more"
        if len(items) > 5:
            return items[:5] + ["+ " + str(len(items) - 5) + " more"]
        else:
            return items

    async def fetch_info_anime_manga(self, ctx, cmd, title): # Gets anime and manga information using Anilist APIv2

        # Outputs MediaStatuses to strings
        MediaStatusToString = {
            # Has completed and is no longer being released
	          'FINISHED': 'Finished',
            # Currently releasing
	          'RELEASING': 'Releasing',
            # To be released at a later date
	          'NOT_YET_RELEASED': 'Not yet released',
            # Ended before the work could be finished
	          'CANCELLED': 'Cancelled'
        }

        #GraphQL query
        query = '''
query ($id: Int, $page: Int, $search: String, $type: MediaType) {
    Page (page: $page, perPage: 10) {
        media (id: $id, search: $search, type: $type) {
            id
            idMal
            description(asHtml: false)
            title {
                english
                romaji
            }
            coverImage {
            		medium
            }
            averageScore
            meanScore
            status
            episodes
            chapters
            externalLinks {
                url
                site
            }
            nextAiringEpisode {
                timeUntilAiring
            }
        }
    }
}
'''
        url = 'https://graphql.anilist.co'
        variables = {
            'search': title,
            'page': 1,
            'type': cmd
        }

        response = requests.post(url, json={'query': query, 'variables': variables})

        medias = response.json()['data']['Page']['media']

        # Counts how many results there is and deals with it based on user input
        result_count = len(medias)
        if result_count == 0:
            return await self.bot.say("I couldn't find anything!")
        else:
            if result_count == 1:
                entry = medias[0]
            else:
                msg = "**Please choose one by giving its number.**\n"
                for i in range(0, len(medias)):
                    msg += "\n{number} - {title_romaji}".format(number=i+1, title_romaji=medias[i]['title']['romaji'])

                message = await self.bot.say(msg)

                check = lambda m: m.content.isdigit() and int(m.content) in range(1, len(medias) + 1)
                resp = await self.bot.wait_for_message(timeout=15, author=ctx.message.author,
                                                       check=check)

                # Deletes messages to not pollute the chat
                await self.bot.delete_message(message)
                if resp:
                   await self.bot.delete_message(resp)
                if resp is None:
                    return

                entry = medias[int(resp.content)-1]

            # Sets up various variables for Embed
            link = 'https://anilist.co/{}/{}'.format(cmd.lower(), entry['id'])
            title = "[{}]({})".format(entry['title']['romaji'], link)
            description = entry['description']
            title = entry['title']['romaji']
            if entry.get('nextAiringEpisode'):
                seconds = entry['nextAiringEpisode']['timeUntilAiring']
                time_left = str(datetime.timedelta(seconds=seconds))
            else:
                time_left = "Never"

            external_links = ""
            for i in range(0, len(entry['externalLinks'])):
              ext_link = entry['externalLinks'][i]
              external_links += "[{site_name}]({link}), ".format(site_name=ext_link['site'], link=ext_link['url'])
              if i+1 == len(entry['externalLinks']):
                external_links = external_links[:-2]

            # Build Embed
            embed = discord.Embed()
            embed.description = self.description_parser(description)
            embed.title = title
            embed.url = link
            embed.set_thumbnail(url=entry['coverImage']['medium'])
            embed.add_field(name="Score", value=entry.get('averageScore', 'N/A'))
            if cmd == "ANIME":
                embed.add_field(name="Episodes", value=entry.get('episodes', 'N/A'))
                embed.set_footer(text="Status : "+ MediaStatusToString[entry['status']] + ", Next episode : " + time_left + ", Powered by Anilist")
            else:
                embed.add_field(name="Chapters", value=entry.get('chapters', 'N/A'))
                embed.set_footer(text="Status : "+ MediaStatusToString.get(entry.get('status'), 'N/A') + ", Powered by Anilist")
            if external_links:
                embed.add_field(name="Streaming and/or Info sites", value=external_links)
            embed.add_field(name="You can find out more", value="[Anilist]({anilist_url}), [MAL](https://myanimelist.net/{type}/{id_mal}), Kitsu (Soon™)".format(id_mal=entry['idMal'], anilist_url=link, type=cmd.lower()))

            await self.bot.say(embed=embed)

    async def fetch_info_user(self, ctx, username): # Gets user information using Anilist APIv2

        #GraphQL query
        query = '''
query ($id: Int, $page: Int, $search: String) {
    Page (page: $page, perPage: 10) {
        users (id: $id, search: $search) {
            id
            name
            siteUrl
            avatar {
                    large
            }
            about (asHtml: true),
            stats {
                watchedTime
                chaptersRead
            }
            favourites {
            manga {
              nodes {
                id
                title {
                  romaji
                  english
                  native
                  userPreferred
                }
              }
            }
            characters {
              nodes {
                id
                name {
                  first
                  last
                  native
                }
              }
            }
            anime {
              nodes {
                id
                title {
                  romaji
                  english
                  native
                  userPreferred
                }
              }
            }
            }
        }
    }
}
'''
        url = 'https://graphql.anilist.co'
        variables = {
            'search': username,
            'page': 1
        }

        response = requests.post(url, json={'query': query, 'variables': variables})

        medias = response.json()['data']['Page']['users']

        # Counts how many results there is and deals with it based on user input
        result_count = len(medias)
        if result_count == 0:
            return await self.bot.say("I couldn't find anything!")
        else:
            if result_count == 1:
                entry = medias[0]
            else:
                msg = "**Please choose one by giving its number.**\n"
                for i in range(0, len(medias)):
                    msg += "\n{number} - {name}".format(number=i+1, name=medias[i]['name'])

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

        # Sets up various variables for Embed
        link = 'https://anilist.co/user/{}'.format(entry['id'])
        title = "[{}]({})".format(entry['name'], link)
        description = self.description_parser(entry['about'])
        title = entry['name']

        # Build Embed
        embed = discord.Embed()
        embed.description = description
        embed.title = title
        embed.url = link
        embed.set_thumbnail(url=entry['avatar']['large'])
        embed.add_field(name="Watched time", value=datetime.timedelta(minutes=int(entry['stats']['watchedTime'])))
        embed.add_field(name="Chapters read", value=entry['stats'].get('chaptersRead', 'N/A'))
        if entry["favourites"]["anime"]:
            fav_anime = ["[{}]({})".format(anime["title"]["userPreferred"], "https://anilist.co/anime/" + str(anime["id"])) for anime in entry["favourites"]["anime"]["nodes"]]
            embed.add_field(name="Favourite anime", value="\n".join(self.list_maximum(fav_anime)))
        if entry["favourites"]["manga"]:
            fav_manga = ["[{}]({})".format(manga["title"]["userPreferred"], "https://anilist.co/manga/" + str(manga["id"])) for manga in entry["favourites"]["manga"]["nodes"]]
            embed.add_field(name="Favourite manga", value="\n".join(self.list_maximum(fav_manga)))
        if entry["favourites"]["characters"]:
            fav_ch = ["[{}]({})".format(self.format_name(character["name"]["first"], character["name"]["last"]), "https://anilist.co/character/" + str(character["id"])) for character in entry["favourites"]["characters"]["nodes"]]
            embed.add_field(name="Favourite characters", value="\n".join(self.list_maximum(fav_ch)))
        embed.set_footer(text="Powered by Anilist")

        await self.bot.say(embed=embed)

    async def fetch_info_character(self, ctx, name): # Gets character information using Anilist APIv2

        #GraphQL query
        query = '''
query ($id: Int, $page: Int, $search: String) {
  Page(page: $page, perPage: 10) {
    characters(id: $id, search: $search) {
      id
      description (asHtml: true),
      name {
        first
        last
        native
      }
      image {
        large
      }
      media {
        nodes {
          id
          type
          title {
            romaji
            english
            native
            userPreferred
          }
        }
      }
    }
  }
}
'''
        url = 'https://graphql.anilist.co'
        variables = {
            'search': name,
            'page': 1
        }

        response = requests.post(url, json={'query': query, 'variables': variables})

        medias = response.json()['data']['Page']['characters']

        # Counts how many results there is and deals with it based on user input
        result_count = len(medias)
        if result_count == 0:
            return await self.bot.say("I couldn't find anything!")
        else:
            if result_count == 1:
                entry = medias[0]
            else:
                msg = "**Please choose one by giving its number.**\n"
                for i in range(0, len(medias)):
                    msg += "\n{number} - {name}".format(number=i+1, name=self.format_name(medias[i]['name']['first'], medias[i]['name']['last']))

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

        # Sets up various variables for Embed
        link = 'https://anilist.co/character/{}'.format(entry['id'])
        character_anime = ["[{}]({})".format(anime["title"]["userPreferred"], "https://anilist.co/anime/" + str(anime["id"])) for anime in entry["media"]["nodes"] if anime["type"] == "ANIME"]
        character_manga = ["[{}]({})".format(manga["title"]["userPreferred"], "https://anilist.co/manga/" + str(manga["id"])) for manga in entry["media"]["nodes"] if manga["type"] == "MANGA"]
        description = self.description_parser(entry['description'])

        # Build Embed
        embed = discord.Embed()
        embed.title = self.format_name(entry['name']['first'], entry['name']['last'])
        embed.description = description
        embed.url = link
        embed.set_thumbnail(url=entry['image']['large'])
        if len(character_anime) > 0:
            embed.add_field(name="Anime", value="\n".join(self.list_maximum(character_anime)))
        if len(character_manga) > 0:
            embed.add_field(name="Manga", value="\n".join(self.list_maximum(character_manga)))
        embed.set_footer(text="Powered by Anilist")

        await self.bot.say(embed=embed)

def setup(bot):
    bot.add_cog(AniSearch(bot))
