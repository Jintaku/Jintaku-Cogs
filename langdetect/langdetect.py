import discord
from discord.ext import commands
from cogs.utils import checks
from datetime import datetime, timedelta
import re
from langdetect import detect

class langdetect:
    """Shows how much french vs english is shown in a channel"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def langdetect(self, ctx, channel, threshold):
        """Simply give the channel id and how many days old the messages can be"""

        if not threshold.isdigit(): # Checks wether the threshold given is a number
            await self.bot.say("Threshold should be numbers. Aborting.")
            return

        msg = await self.bot.say("Processing please wait...")
        await self.get_messages(ctx.message.server, channel, int(threshold))
        await self.bot.delete_message(msg)

    async def get_messages(self, server, channel, threshold): # Gets messages and detects the language
        after_n_days_ago = datetime.utcnow() - timedelta(days=threshold)
        channel_id = self.bot.get_channel(str(channel))
        frcounter = 0
        encounter = 0
        async for mesg in self.bot.logs_from(channel_id, after=after_n_days_ago, limit=100*100, reverse=True):
            mesg = mesg.clean_content
            cleantext = self.letters(mesg)
            if cleantext == "" or cleantext == None or type(cleantext) != str or cleantext.isspace() == True:
                pass
            else:
                if detect(cleantext) == 'fr':
                    frcounter = frcounter + 1
                if detect(cleantext) == 'en':
                    encounter = encounter + 1
        await self.bot.say("French : {} \nEnglish : {}".format(frcounter, encounter))

    def letters(self, mesg): # Cleans messages to remove non_alphanumeric characters
        valids = []
        for character in mesg:
            if character.isspace():
                valids.append(character)
            if character.isalpha():
                valids.append(character)
        cleantext = ''.join(valids)
        return cleantext

def setup(bot):
    bot.add_cog(langdetect(bot))
