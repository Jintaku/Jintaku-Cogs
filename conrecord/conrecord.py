import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from cogs.utils import checks
import os
from datetime import datetime, timedelta

class conrecord:
    """Record a conversation and put it in a file"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def conrecord(self, ctx, channel, threshold):
        """Simply give the channel id and how many days old the messages can be"""

        if not threshold.isdigit(): # Checks wether the threshold given is a number
            await self.bot.say("Threshold should be numbers. Aborting.")
            return

        msg = await self.bot.say("Processing please wait...")
        await self.get_messages(ctx.message.server, channel, int(threshold))
        await self.bot.delete_message(msg)

    async def get_messages(self, server, channel, threshold): # Gets messages and saves them to the file
        after_n_days_ago = datetime.utcnow() - timedelta(days=threshold)
        channel_id = self.bot.get_channel(str(channel))
        with open("data/conrecord/{}.txt".format(datetime.utcnow().date().isoformat()), "w") as f:
            async for mesg in self.bot.logs_from(channel_id, after=after_n_days_ago, limit=100*100, reverse=True):
                message = "{} : {}".format(mesg.author, mesg.clean_content)
                print(message)
                f.write(message + "\n")
            f.flush()
            f.close()

def check_folders():
    if not os.path.exists("data/conrecord"):
        print("Creating data/conrecord folder...")
        os.makedirs("data/conrecord")

def setup(bot):
    check_folders()
    bot.add_cog(conrecord(bot))
