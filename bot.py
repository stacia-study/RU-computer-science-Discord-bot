from __future__ import annotations

import os
import contextlib
import asyncpg
import aiohttp
import discord
import logging
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv

from utils.views import RURolePersistentView

load_dotenv()

initial_extensions = [
    'cogs.admin',
    'cogs.events',
    'cogs.errors',
    'cogs.jishaku',
    # 'tags', # wait for update
    'cogs.misc',
    'cogs.computer_science',
]

_log = logging.getLogger('RU_COMSCI_BOT')

# jishaku
os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
os.environ['JISHAKU_HIDE'] = 'True'

# intents
intents = discord.Intents.all()

# allowed_mentions
allowed_mentions = discord.AllowedMentions(roles=True, users=True, everyone=False)

def _prefix_callable(bot: RU_COMSCI_bot, msg: discord.Message):
    user_id = bot.user.id
    return [f'<@!{user_id}> ', f'<@{user_id}> ', '!', '.', '?']

class RU_COMSCI_bot(commands.Bot):
    pool: asyncpg.Pool
    bot_app_info: discord.AppInfo

    def __init__(self) -> None:
        super().__init__(
            command_prefix=_prefix_callable,
            help_command=None,
            case_insensitive=True,
            allowed_mentions=allowed_mentions,
            intents=intents,
            application_id=994900112637706260,
        )

        # bot info stuff
        self.launch_time = f'<t:{round(datetime.now().timestamp())}:R>'
        self.maintenance = False
        self._version = '1.0.0a'
        self.theme = 0xC3B1E1
        self.last_update = datetime(2022, 7, 8)

        # http
        self.session = None

        # activity
        self.bot_activity = 'Computer Science :)'

        # owner ids
        self.owner_ids = [240059262297047041]  # หาเพื่อนพัฒนาบอท ;-;)

        # cache
        self.initial_extensions = initial_extensions

    async def interaction_check(self, interaction: discord.Interaction) -> bool:

        if interaction.user.id in self.owner_ids:
            return True

        if not self.maintenance:  # if bot is in maintenance mode
            return True

        return False

    async def set_bot_activity(self) -> None:
        """ Sets the bot activity. """

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=self.bot_activity)
        )

    async def on_ready(self) -> None:
        """ Called when the bot is ready. """

        await self.set_bot_activity()

        await self.tree.sync()

        print(
            f"\n\nLogged in as: {self.user}"
            f"\nActivity: {self.bot_activity}"
            f"\nServers: {len(self.guilds)}"
            f"\nUsers: {sum(g.member_count for g in self.guilds)}"
        )

    async def load_cogs(self) -> None:
        """ Loads all cogs. """
        for ext in initial_extensions:
            try:
                await self.load_extension(ext)
            except Exception as e:
                _log.error(f'Failed to load extension {ext}.', exc_info=True)

    async def setup_hook(self) -> None:
        if self.session is None:
            self.session = aiohttp.ClientSession()
        self.bot_app_info = await self.application_info()
        self.owner_id = self.bot_app_info.owner.id
        await self.load_cogs()

        # add view role
        self.add_view(RURolePersistentView())

    async def close(self) -> None:
        await super().close()
        await self.pool.close()
        await self.session.close()

    async def start(self) -> None:
        return await super().start(os.getenv('DISCORD_TOKEN'), reconnect=True)
