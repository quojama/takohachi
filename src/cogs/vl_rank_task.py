import asyncio
import json
import sqlite3
from datetime import datetime, timedelta, timezone

import discord
import httpx
from discord.ext import commands, tasks

from cogs.valorant_api import current_season, season_txt


class RankTasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.index = 0
        self.bot = bot
        self.printer.start()

    def cog_unload(self):
        self.printer.cancel()

    @tasks.loop(seconds=600.0)
    async def printer(self):
        channel = self.bot.get_channel(int("924924594706583562"))

        # タイムゾーンの生成
        JST = timezone(timedelta(hours=+9), "JST")
        today = datetime.now(JST)

        this_month = today.month
        this_day = today.day
        this_hour = today.hour
        this_minute = today.minute

        if this_hour == 7 and 0 <= this_minute <= 9:

            DB_DIRECTORY = "/data/takohachi.db"

            # データベースに接続とカーソルの取得
            conn = sqlite3.connect(DB_DIRECTORY)
            cur = conn.cursor()

            # レコードを全て取得し、yesterday_eloで降順にソート
            cur.execute("SELECT * FROM val_puuids ORDER BY yesterday_elo DESC")
            rows = cur.fetchall()

            async def fetch(row):
                puuid, region, name, tag, yesterday_elo = row

                # 非同期でリクエスト
                try:
                    url = f"https://api.henrikdev.xyz/valorant/v2/by-puuid/mmr/{region}/{puuid}"
                    async with httpx.AsyncClient() as client:
                        response = await client.get(url, timeout=60)
                except httpx.HTTPError as e:
                    return

                # APIから必要な値を取得
                data = response.json()
                currenttierpatched = data['data']['current_data']['currenttierpatched']
                ranking_in_tier = data['data']['current_data']['ranking_in_tier']
                elo: int = data['data']['current_data']['elo']
                name = data['data']['name']
                tag = data['data']['tag']

                try:
                    current_season_data = data['data']['by_season'][current_season]
                except KeyError:
                    win_loses = "-W/-L"

                final_rank_patched = current_season_data.get('final_rank_patched', "Unrated")

                if final_rank_patched == "Unrated":
                    win_loses = "-W/-L"
                else:
                    wins: int = current_season_data.get('wins', 0)
                    number_of_games: int = current_season_data.get('number_of_games', 0)
                    loses: int = number_of_games - wins
                    win_loses = f"{wins}W/{loses}L"

                if win_loses == "-W/-L":
                    current_rank_info = "Unranked"
                    todays_elo: int = 0
                else:
                    current_rank_info = f"{currenttierpatched} (+{ranking_in_tier})"
                    todays_elo: int = elo - yesterday_elo

                # todays_eloの値に応じて絵文字を選択
                if todays_elo > 0:
                    emoji = "<a:p10_jppy_verygood:984636995752046673>"
                    plusminus = "+"
                elif todays_elo < 0:
                    emoji = "<a:p10_jppy_bad:984637001867329586>"
                    plusminus = ""
                else:
                    emoji = "<a:p10_jppy_soso:984636999799541760>"
                    plusminus = "±"

                # フォーマットに合わせて整形
                result_string = f"{emoji} `{name} #{tag}`\n- {current_rank_info}\n- 前日比: {plusminus}{todays_elo}\n- {win_loses}\n\n"

                # DBの情報を今日の取得内容で更新
                cur.execute("UPDATE val_puuids SET name=?, tag=?, yesterday_elo=? WHERE puuid=?", (name, tag, elo, puuid))
                conn.commit()

                return result_string

            async def main():
                tasks = [fetch(row) for row in rows]
                output = await asyncio.gather(*tasks)
                join = "".join(output)
                return join

            join = await main()

            embed = discord.Embed()
            embed.set_footer(text=season_txt)
            embed.color = discord.Color.purple()
            embed.title = f"みんなの昨日の活動です。"
            embed.description = f"{join}"
            await channel.send(embed=embed)

            conn.close()

    # デプロイ後Botが完全に起動してからタスクを回す
    @printer.before_loop
    async def before_printer(self):
        print("waiting until bot booting")
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(RankTasks(bot))
