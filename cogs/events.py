from __future__ import annotations

import discord
from discord import Interaction
from discord.ext import commands, tasks
from typing import Union, TYPE_CHECKING
from datetime import time, datetime

if TYPE_CHECKING:
    from bot import RU_COMSCI_bot


class Event(commands.Cog):
    """Bot Events"""

    def __init__(self, bot: RU_COMSCI_bot) -> None:
        self.bot: RU_COMSCI_bot = bot


async def setup(bot: RU_COMSCI_bot) -> None:
    await bot.add_cog(Event(bot))
