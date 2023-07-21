import discord
import httpx
from discord import app_commands
from discord.ext import commands

current_season = "e7a1"
season_txt = current_season.replace("e", "Episode ").replace("a", " Act ")


class Valo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="vr", description="Valorantのランクなどを表示します。")
    @app_commands.describe(
        name="Valorantのプレイヤー名を入れてください。ex) 植 物、ウィングマン太郎、The Manなど",
        tagline="#以降のタグを入れてください。#は不要です。",
    )

    # API request
    # APIリクエストを送信し、エラーをチェックする関数
    async def vr(self, interaction: discord.Interaction, name: str, tagline: str):
        # interactionは3秒以内にレスポンスしないといけないとエラーになるのでこの処理を入れる。
        await interaction.response.defer()

        async def send_request(url, name, tagline):
            async with httpx.AsyncClient() as client:
                res = await client.get(url, timeout=10)

            data = res.json()

            # statusが200以外の場合はエラーを返す。
            if data["status"] != 200:
                embed = discord.Embed()
                embed.color = discord.Color.red()
                embed.title = "<:p01_pepebrim:951023068275421235>:warning: 入力が間違えているかもしれません。"
                embed.description = f'**あなたの入力:** {name}#{tagline}\n**Status Code:** {data["status"]}\n\
                **Error Msg:** {data["errors"][0]["message"]}'
                await interaction.followup.send(embed=embed)
                return None

            return data

        # URLのエンドポイント
        rank_url = f"https://api.henrikdev.xyz/valorant/v2/mmr/ap/{name}/{tagline}"
        account_url = f"https://api.henrikdev.xyz/valorant/v1/account/{name}/{tagline}"
        lifetime_matches_url = (
            f"https://api.henrikdev.xyz/valorant/v1/lifetime/matches/ap/{name}/{tagline}"
        )

        try:
            # リクエストを送信
            data = await send_request(rank_url, name, tagline)
            if data is None:  # エラーチェック
                return

            account_data = await send_request(account_url, name, tagline)
            if account_data is None:  # エラーチェック
                return

            match_data = await send_request(lifetime_matches_url, name, tagline)
            if match_data is None:  # エラーチェック
                return

        except httpx.HTTPError as e:
            await interaction.followup.send(f"⚠ APIリクエストエラーが発生しました。時間を置いて試してみてください。: {e}")

        # APIから必要な基本情報の値を取得
        currenttierpatched = data["data"]["current_data"]["currenttierpatched"]
        ranking_in_tier = data["data"]["current_data"]["ranking_in_tier"]
        name = data["data"]["name"]
        tag = data["data"]["tag"]
        rank_image_url = data["data"]["current_data"]["images"]["small"]
        account_level = account_data["data"]["account_level"]
        card_image_url = account_data["data"]["card"]["wide"]

        # 新シーズンになって1試合もやってない場合は
        # アクトごとのレスポンス部分はKeyErrorが発生するのでその判定を行う
        try:
            current_season_data = data["data"]["by_season"][current_season]
            final_rank_patched = current_season_data.get("final_rank_patched", "Unrated")
            number_of_games: int = current_season_data.get("number_of_games", 0)
            # 正確なwinsを取得するために変更
            wins: int = len(data["data"]["by_season"][current_season]["act_rank_wins"])
            loses: int = number_of_games - wins
        except KeyError:
            wins = 0
            loses = 0
            final_rank_patched = "Unrated"

        # ランクがUnratedの場合はELOなども一旦0にする。
        # Unratedではなくランクがついている場合は通常の処理。
        if final_rank_patched == "Unrated":
            currenttierpatched = "Unrated"
            ranking_in_tier = 0
            rank_image_url = "https://media.valorant-api.com/competitivetiers/564d8e28-c226-3180-6285-e48a390db8b1/0/smallicon.png"
        else:
            pass

        # これまでのランクすべてのWLを取得
        total_act_rank_wins = 0
        total_number_of_games = 0
        season_data = data["data"]["by_season"]

        for season, info in season_data.items():
            if "act_rank_wins" in info:
                total_act_rank_wins += len(info["act_rank_wins"])
            if "number_of_games" in info:
                total_number_of_games += info["number_of_games"]
        total_act_rank_loses = total_number_of_games - total_act_rank_wins

        # これまでの全試合のhead率を取得
        total_head, total_body, total_leg = 0, 0, 0

        for match in match_data["data"]:
            shots = match["stats"]["shots"]
            total_head += shots["head"]
            total_body += shots["body"]
            total_leg += shots["leg"]

        total_shots = total_head + total_body + total_leg
        head_rate = round((total_head / total_shots) * 100, 2)

        # embed書き込み処理
        embed = discord.Embed()
        embed.title = f"{name} `#{tag}`"
        embed.color = discord.Color.magenta()
        embed.description = f"{season_txt} competitive results"
        embed.set_thumbnail(url=rank_image_url)

        embed.add_field(
            name="Current Rank", value=f"```{currenttierpatched} (+{ranking_in_tier})```"
        )
        embed.add_field(name="Current Act W/L", value=f"```{wins}W/{loses}L```")
        embed.add_field(
            name="Lifetime W/L", value=f"```{total_act_rank_wins}W/{total_act_rank_loses}L```"
        )
        embed.add_field(name="Lifetime HS Rate", value=f"```{head_rate}%```")
        embed.add_field(name="Account Level", value=f"```{account_level}```")
        embed.set_footer(
            text="※ WLはランクのみの集計です。\n※ 引き分けは負けとしてカウントされます。\n※ ヘッショ率は過去100試合くらいのアンレやコンペすべての試合から算出しています。\n※ またキルしたショットではなく敵に当たった弾すべてでカウントしています。"  # noqa E501
        )
        embed.set_image(url=card_image_url)

        # interaction.response.deferを使ったのでここはfollowup.sendが必要
        await interaction.followup.send(embed=embed)
        return

    # Valorantの最新ニュースを取ってくるコマンド
    @app_commands.command(name="vnews", description="Valorantの最新ニュースを取得します。")
    async def vnews(self, interaction: discord.Interaction):
        # interactionは3秒以内にレスポンスしないといけないとエラーになるのでこの処理で待たせる。
        await interaction.response.defer()

        news_url = "https://api.henrikdev.xyz/valorant/v1/website/ja-jp"
        async with httpx.AsyncClient() as client:
            res = await client.get(news_url)
        json = res.json()

        news_01_title = json["data"][0]["title"]
        news_01_url = json["data"][0]["url"]
        news_01_external = json["data"][0]["external_link"]
        news_01_image = json["data"][0]["banner_url"]

        news_02_title = json["data"][1]["title"]
        news_02_url = json["data"][1]["url"]
        news_02_external = json["data"][1]["external_link"]

        news_03_title = json["data"][2]["title"]
        news_03_url = json["data"][2]["url"]
        news_03_external = json["data"][2]["external_link"]

        news_04_title = json["data"][3]["title"]
        news_04_url = json["data"][3]["url"]
        news_04_external = json["data"][3]["external_link"]

        if news_01_external is not None:
            news_01_url = news_01_external
        if news_02_external is not None:
            news_02_url = news_02_external
        if news_03_external is not None:
            news_03_url = news_03_external
        if news_01_external is not None:
            news_04_url = news_04_external

        # Embed
        embed = discord.Embed()
        embed.title = "Valorant Latest News"
        embed.color = discord.Color.purple()
        embed.description = f"- [{news_01_title}]({news_01_url})\n\n- \
            [{news_02_title}]({news_02_url})\n\n- [{news_03_title}]({news_03_url})\n\n- [{news_04_title}]({news_04_url})\n"
        embed.set_image(url=news_01_image)

        # interaction.response.deferを使ったのでここはfollowup.sendが必要
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Valo(bot), guilds=[discord.Object(id=731366036649279518)])
