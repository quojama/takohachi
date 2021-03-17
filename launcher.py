from discord.ext import commands
import config
import asyncio
import discord


bot = commands.Bot(command_prefix="!!")


@bot.event
async def on_ready():
    print("Yeah!_bot_is_on_ready")
    return

@bot.command()
async def playing(ctx, title):
    client = bot
    game = discord.Game(name=title)
    await client.change_presence(activity=game)


bot.load_extension("dispander") #diapanderをextensionとして読み込み
bot.load_extension("cogs.tanaka")
bot.load_extension("cogs.marimo")
bot.load_extension("cogs.yobro")
bot.load_extension("cogs.vcalert")
bot.load_extension("cogs.greet")
bot.load_extension("cogs.notify")

bot.run(config.TOKEN)