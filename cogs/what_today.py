from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands
from libs.utils import get_what_today


class WhatToday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def whatToday(self, ctx):
        # タイムゾーンの生成
        JST = timezone(timedelta(hours=+9), 'JST')

        today = datetime.now(JST)

        this_month = today.month
        this_day = today.day

        result = get_what_today(this_month, this_day)

        embed = discord.Embed()
        embed.timestamp = datetime.now(JST)
        embed.color = discord.Color.green()
        embed.title = f'日はなんの日？'
        embed.description = f"{this_month}月{this_day}日\n{result}"
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(WhatToday(bot))
