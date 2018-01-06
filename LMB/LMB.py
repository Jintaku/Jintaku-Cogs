import discord
from discord.ext import commands
from cogs.utils import checks
from datetime import datetime, timedelta

class LMB:
    """Show stuff using osu!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def lmb(self, ctx, green_threshold, gray_threshold):
        """Shows a board containing users and the date of their last message! \n \n Colors : \n Green : Those whose last message was sent in the first period of time stated \n Grey : Those whose last message was in the second period of time stated \n Red : Those are in neither categories"""

        if not green_threshold.isdigit() or not gray_threshold.isdigit():
            await self.bot.say("Thresholds should be numbers. Aborting.")
            return

        msg = await self.bot.say("Processing please wait...")
        green_users = await self.get_green_users(ctx.message.server, int(green_threshold))
        await self.bot.delete_message(msg)
        await self.print_user_box(green_users, "+")

        msg = await self.bot.say("Processing please wait...")
        gray_users = await self.get_gray_users(ctx.message.server, green_users, int(green_threshold), int(gray_threshold))
        await self.bot.delete_message(msg)
        await self.print_user_box(gray_users, "---")

        msg = await self.bot.say("Processing please wait...")
        red_users = await self.get_red_users(ctx.message.server, green_users, gray_users)
        await self.bot.delete_message(msg)
        await self.print_user_box(red_users, "-")

    async def print_user_box(self, user_list, prefix):
        msg = ""
        char_count = 0
        for user, timestamp in user_list.items():
            if timestamp != datetime.min:
                msg += prefix + user + " [" + timestamp.strftime('%Y-%m-%d') + "]" + "\n"
            else:
                msg += prefix + user + "\n"
            char_count += len(user)
            if char_count > 1000:
                await self.bot.say("```diff\n" + msg + "```")
                msg = ""
                char_count = 0
        if msg != "":
            await self.bot.say("```diff\n" + msg + "```")

    def user_as_string(self, user):
        return user.name + "#" + user.discriminator

    async def get_green_users(self, server, green_threshold):
        after_n_days_ago = datetime.utcnow() - timedelta(days=green_threshold)
        users = {}
        for channel in server.channels:
            async for msg in self.bot.logs_from(channel, after=after_n_days_ago, limit=100*100, reverse=True):
                if msg.timestamp >= users.get(msg.author.id, msg).timestamp:
                    users[msg.author.id] = msg
        return {self.user_as_string(msg.author): msg.timestamp for msg in users.values()}

    async def get_gray_users(self, server, green_users, green_threshold, gray_threshold):
        before_n_days_ago = datetime.utcnow() - timedelta(days=green_threshold)
        after_n_days_ago = datetime.utcnow() - timedelta(days=gray_threshold)
        users = {}
        for channel in server.channels:
            async for msg in self.bot.logs_from(channel, before=before_n_days_ago, after=after_n_days_ago, limit=100*100, reverse=True):
                if msg.timestamp >= users.get(msg.author.id, msg).timestamp:
                    users[msg.author.id] = msg
        gray_users = {self.user_as_string(msg.author): msg.timestamp for msg in users.values()}
        return {user: timestamp for user, timestamp in gray_users.items() if user not in green_users.keys()}

    async def get_red_users(self, server, green_users, gray_users):
        red_users = {}
        for user in server.members:
            userstr = self.user_as_string(user)
            if userstr not in green_users.keys() and userstr not in gray_users.keys():
                red_users[userstr] = datetime.min
        return red_users

def setup(bot):
    bot.add_cog(LMB(bot))
