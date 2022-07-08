from __future__ import annotations

import discord
import platform
import pygit2
import itertools
import datetime
import psutil

from discord import Interaction, app_commands
from discord.utils import format_dt, utcnow
from discord.ext import commands
from utils.useful import count_python

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot import RU_COMSCI_bot


def format_commit(commit) -> str:
    short, _, _ = commit.message.partition('\n')
    short = short[0:40] + '...' if len(short) > 40 else short
    short_sha2 = commit.hex[0:6]
    commit_tz = datetime.timezone(datetime.timedelta(minutes=commit.commit_time_offset))
    commit_time = datetime.datetime.fromtimestamp(commit.commit_time).astimezone(commit_tz)
    offset = format_dt(commit_time, style='R')
    return f'[`{short_sha2}`](https://github.com/stacia-study/RU-computer-science-Discord-bot/commits/{commit.hex}) {short} ({offset})'


def get_latest_commits(limit: int = 5) -> str:
    repo = pygit2.Repository('./.git')
    commits = list(itertools.islice(repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL), limit))
    return '\n'.join(format_commit(c) for c in commits)


class Misc(commands.Cog):
    """Miscellaneous commands"""

    def __init__(self, bot: RU_COMSCI_bot) -> None:
        self.bot: RU_COMSCI_bot = bot

    process = psutil.Process()

    @app_commands.command()
    async def ping(self, interaction: Interaction) -> None:
        """ดูปิงของบอท / Show Bot latency."""
        latency = self.bot.latency * 1000
        embed = discord.Embed(color=self.bot.theme)
        embed.add_field(name=f"Latency", value=f"```nim\n{round(latency)} ms```")
        embed.set_footer(text=f'{self.bot.user.name} | v{self.bot._version}', icon_url=self.bot.user.avatar)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='about')
    async def about(self, interaction: Interaction) -> None:
        """ข้อมูลเกี่ยวกับบอท / Shows basic information"""

        bot_version = self.bot._version
        memory_usage = self.process.memory_full_info().uss / 1024 / 1024

        embed = discord.Embed(color=self.bot.theme, timestamp=discord.utils.utcnow())
        embed.set_author(name=f"About Me", icon_url=self.bot.user.avatar)
        embed.add_field(name='Latest updates:', value=get_latest_commits(5), inline=False)

        embed.add_field(
            name='Bot info:',
            value=f"<a:cursor:896576387002032159> Line count: `{count_python('.')}`\n" \
                  f"<:botTag:230105988211015680> Version: `{bot_version}`\n" \
                  f"<:Python:881421088763047946> Python: `{platform.python_version()}`\n" \
                  f"<:dpy:596577034537402378> Discord.py: `{discord.__version__}`",
            inline=True
        )
        embed.add_field(name='\u200b', value='\u200b', inline=True)
        embed.add_field(name='Process:',
                        value=f"OS: `{platform.system()}`\nCPU Usage: `{psutil.cpu_percent()}%`\nMemory Usage: `{memory_usage:.2f} MB`",
                        inline=True)
        embed.add_field(name='Uptime:', value=f"{self.bot.launch_time}", inline=True)
        embed.add_field(name='\u200b', value='\u200b', inline=True)

        await interaction.response.send_message(embed=embed)


async def setup(bot: RU_COMSCI_bot):
    await bot.add_cog(Misc(bot))
