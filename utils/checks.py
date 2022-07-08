import discord
from discord import app_commands
from typing import Optional

__all__ = (
    "owner_devs",
    "cooldown_5s",
    "cooldown_10s"
)


def owner_devs() -> app_commands.check:
    async def actual_check(interaction: discord.Interaction) -> bool:
        if interaction.user.id in interaction.client.owner_ids:
            return True
        return False

    return app_commands.check(actual_check)


def cooldown_5s(interaction: discord.Interaction) -> Optional[app_commands.Cooldown]:
    if interaction.user == interaction.client.owner:
        return None
    return app_commands.Cooldown(1, 5)


def cooldown_10s(interaction: discord.Interaction) -> Optional[app_commands.Cooldown]:
    if interaction.user == interaction.client.owner:
        return None
    return app_commands.Cooldown(1, 10)
