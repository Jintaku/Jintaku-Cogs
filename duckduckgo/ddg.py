import discord
from discord.ext import commands
import aiohttp


class ddg:
    """Search duckduckgo API for instant answers"""


    def __init__(self, bot):
        self.bot = bot

        self.BANNED_ANSWER_TYPES = (
            "ip",
        )

    @commands.command(pass_context=True)
    async def ddg(self, ctx, *, query):
        """Search ddg API for instant answers"""

        ddg = await self.query_ddg(query)
        if not ddg:
            await self.bot.say("I couldn't find anything.")
            return

        if ddg["Type"] in ("C", "D"):
            choices = []
            counter = 0
            for related_topic in ddg["RelatedTopics"]:
                if "Topics" in related_topic.keys():
                    for sub_topic in related_topic["Topics"]:
                        counter += 1
                        choices.append((counter, sub_topic["FirstURL"], sub_topic["Text"]))
                else:
                    counter += 1
                    choices.append((counter, related_topic["FirstURL"], related_topic["Text"]))

            msg = "**Please choose one by giving its number.**\n"
            msg += "\n".join(["{number} - {desc}".format(number=number, desc=desc) for number, _, desc in choices])
            message = await self.bot.say(msg)

            check = lambda m: m.content.isdigit() and int(m.content) in range(1, len(choices) + 1)
            resp = await self.bot.wait_for_message(timeout=15, author=ctx.message.author, check=check)

            # Deletes messages to not pollute the chat
            await self.bot.delete_message(message)
            if resp:
               await self.bot.delete_message(resp)
            if resp is None:
                return

            _, entry, _ = choices[int(resp.content)-1]
            new_query = entry.split("/")[-1].replace("_", " ")
            ddg = await self.query_ddg(new_query)
            if ddg["Type"] != "A":
                await self.bot.say("I couldn't find anything.")
                return
            else:
                await self.show_article(ddg)
        else:
            await self.show_article(ddg)

    async def query_ddg(self, query):
        ddg = None
        async with aiohttp.get("https://api.duckduckgo.com/?skip_disambig=1&q=" + query.replace(" ", "+") + "&format=json") as response:
            try:
                ddg = await response.json()
            except ValueError:
                return None
        if ddg["AnswerType"] in self.BANNED_ANSWER_TYPES:
            return None
        empty = True
        for key, value in ddg.items():
            if key == "Type":
                continue
            if value:
                empty = False
        if empty:
            return None
        return ddg

    async def show_article(self, ddg):
        # Build Embed
        embed = discord.Embed()
        embed.description = ddg["AbstractText"] or ddg["Answer"] or ddg["Definition"]
        embed.title = ddg["Heading"] or ddg["AbstractSource"] or ddg["DefinitionSource"]
        embed.url = ddg["AbstractURL"] or ddg["DefinitionURL"]
        if ddg["Image"]:
            embed.set_thumbnail(url=ddg["Image"])
        embed.set_footer(text="Powered by Duckduckgo instant answers API")

        await self.bot.say(embed=embed)

def setup(bot):
    bot.add_cog(ddg(bot))

"""
{
Abstract: ""
AbstractText: ""
AbstractSource: ""
AbstractURL: ""
Image: ""
Heading: ""
Answer: ""
Redirect: ""
AnswerType: ""
Definition: ""
DefinitionSource: ""
DefinitionURL: ""
RelatedTopics: [ ]
Results: [ ]
Type: ""
}
"""
