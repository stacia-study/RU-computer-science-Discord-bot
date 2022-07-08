from __future__ import annotations

import discord
from discord.ext import commands
from typing import Literal, Union, TYPE_CHECKING
from datetime import time, datetime

from jishaku.codeblocks import codeblock_converter

from utils.errors import RUBotError

if TYPE_CHECKING:
    from bot import RU_COMSCI_bot


class ComputerScience(commands.Cog):
    """Computer Science commands"""

    def __init__(self, bot: RU_COMSCI_bot) -> None:
        self.bot: RU_COMSCI_bot = bot

    # todo design
    # add choice ['decode', 'encode'] or not ?

    # @commands.hybrid_command(aliases=['bin'])
    # async def binary(self, ctx: commands.Context, *, texts: str):
    #     """ แปลงข้อความเป็นเลขฐาน 2 """
    #     ...
    #
    # @commands.hybrid_command(aliases=['hex'])
    # async def hexadecimal(self, ctx: commands.Context, *, texts: str):
    #     """ แปลงข้อความเป็นเลขฐาน 16 """
    #     ...
    #
    # @commands.hybrid_command(aliases=['oct'])
    # async def octal(self, ctx: commands.Context, *, texts: str):
    #     """ แปลงข้อความเป็นเลขฐาน 8 """
    #     ...
    #
    # @commands.hybrid_command(aliases=['dec'])
    # async def decimal(self, ctx: commands.Context, *, texts: str):
    #     """ แปลงข้อความเป็นเลขฐาน 10 """
    #     ...

    @commands.hybrid_command(aliases=['py'])
    async def python(self, ctx: commands.Context, *, code: str):
        """ jishaku py"""
        jsk = self.bot.get_command("jishaku py")
        await jsk(ctx, argument=codeblock_converter(code))

    @commands.hybrid_command(aliases=['cal'])
    async def calculate(self, ctx: commands.Context, *, equation: str):
        """ เครื่องคิดเลข """

        if not equation:
            raise RUBotError('กรุณาระบุข้อความที่ต้องการแปลง')

        try:
            result = eval(equation)
        except Exception as e:
            raise RUBotError(f'ไม่สามารถคำนวนได้: {e}')

        embed = discord.Embed(
            title='Calculate',
            description=f'{equation}\n```{result}```',
        )
        await ctx.reply(embed=embed, allowed_mentions=discord.AllowedMentions().none())

async def setup(bot: RU_COMSCI_bot):
    await bot.add_cog(ComputerScience(bot))
