import random
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands, tasks

from libs.utils import get_stock_price, get_trivia, get_weather, get_what_today


class WTTasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.index = 0
        self.bot = bot
        self.printer.start()

    def cog_unload(self):
        self.printer.cancel()

    @tasks.loop(seconds=600.0)
    async def printer(self):
        channel = self.bot.get_channel(int("762575939623452682"))

        # タイムゾーンの生成
        JST = timezone(timedelta(hours=+9), "JST")
        today = datetime.now(JST)

        this_month = today.month
        this_day = today.day
        this_hour = today.hour
        this_minute = today.minute

        if this_hour == 7 and 0 <= this_minute <= 9:
            result = get_what_today(this_month, this_day)

            # 東京地方の天気を取得。citycode一覧 "https://weather.tsukumijima.net/primary_area.xml"
            citycode = "130010"
            tokyo_weather = get_weather(citycode)

            # 山形の天気を取得。
            citycode = "060010"
            yamagata_weather = get_weather(citycode)

            # ChatGPTで雑学を取得
            trivia = await get_trivia()
            good_morning = random.choice(["おざし。", "おざす。", "お。", "おはようございます。"])

            # USD/JPY
            ticker_symbol = "USDJPY=X"
            usd_jpy_day_before_ratio, usd_jpy_stock_today = get_stock_price(ticker_symbol)

            # 日経平均
            ticker_symbol = "^N225"
            nikkei_day_before_ratio, nikkei_stock_today = get_stock_price(ticker_symbol)

            # S&P500
            ticker_symbol = "^GSPC"
            sp500_day_before_ratio, sp500_stock_today = get_stock_price(ticker_symbol)

            # NASDAQ
            ticker_symbol = "^IXIC"
            nasdaq_day_before_ratio, nasdaq_stock_today = get_stock_price(ticker_symbol)

            # 丸千代山岡家
            ticker_symbol = "3399.T"
            yamaokaya_day_before_ratio, yamaokaya_stock_today = get_stock_price(ticker_symbol)

            # 東京地下鉄株式会社
            ticker_symbol = "9023.T"
            metro_day_before_ratio, metro_stock_today = get_stock_price(ticker_symbol)

            market_text = f"- :moneybag: **USD/JPY:** {round(usd_jpy_stock_today, 1):,}円 ({usd_jpy_day_before_ratio})\n- :flag_jp: **日経225:** {round(nikkei_stock_today, 1):,}円 ({nikkei_day_before_ratio})\n- :flag_us: **S&P500:** {round(sp500_stock_today, 1):,}pt ({sp500_day_before_ratio})\n- :flag_us: **NASDAQ:** {round(nasdaq_stock_today, 1):,}pt ({nasdaq_day_before_ratio})\n- :ramen: **丸千代山岡家:** {round(yamaokaya_stock_today, 1):,}円 ({yamaokaya_day_before_ratio})\n- :metro: **東京地下鉄:** {round(metro_stock_today, 1):,}円 ({metro_day_before_ratio})\n※()内は前日比。"  # noqa: E501

            embed = discord.Embed()
            embed.color = discord.Color.green()
            embed.title = f"{good_morning}{this_month}月{this_day}日 朝の7時です。"
            embed.description = f"### 💡 今日はなんの日？\n{result}\n### 📚 今日の雑学\n{trivia}\n(Powered by [gpt-4o](https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo))\n### 💹 相場\n{market_text}\n### ⛅ 今日の天気\n{tokyo_weather}\n{yamagata_weather}"  # noqa: E501
            await channel.send(embed=embed)

    # デプロイ後Botが完全に起動してからタスクを回す
    @printer.before_loop
    async def before_printer(self):
        print("waiting until bot booting")
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(WTTasks(bot))
