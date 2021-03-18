from discord.ext import commands
import config
import asyncio
import discord

class VC_test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        
        #省きたいチャンネルidを入力
        not_01 = self.bot.get_channel(803245850616791040) #music club vc
        not_02 = self.bot.get_channel(801064070399787028) #system vc
        #not_03 = self.bot.get_channel()
        #not_04 = self.bot.get_channel()
        #not_05 = self.bot.get_channel()

        #除外チャンネルの場合はreturn
        if after.channel in [not_01, not_02]:
            return

        else:
            if after.channel and len(after.channel.members) == 1:
                #メッセージを送るテキストチャンネルID
                channel_id = 821804359700185088
                text_channel = self.bot.get_channel(channel_id)
                await text_channel.send(f"**{member.nick}** が **{after.channel.name}** をはじめました")


def setup(bot):
    bot.add_cog(VC_test(bot))