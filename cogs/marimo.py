from discord.ext import commands
import config
import discord
import asyncio
import datetime
from datetime import timedelta


class Marimo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def mt(self, ctx):
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4)))
        await ctx.send(f"marimo time = {now.strftime('**%m/%d %H:%M**')} ")


def setup(bot):
    bot.add_cog(Marimo(bot))