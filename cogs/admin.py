from __future__ import annotations

import discord
from discord import app_commands, Interaction
from discord.ext import commands
from typing import List, Literal, TYPE_CHECKING

from utils.views import RURolePersistentView

if TYPE_CHECKING:
    from bot import RU_COMSCI_bot

def owner_only() -> app_commands.check:
    async def actual_check(interaction: Interaction):
        return await interaction.client.is_owner(interaction.user)

    return app_commands.check(actual_check)


class Admin(commands.Cog):
    """Admin commands"""

    def __init__(self, bot: RU_COMSCI_bot) -> None:
        self.bot: RU_COMSCI_bot = bot

    @app_commands.command()
    @owner_only()
    async def prepare(self, interaction: Interaction):
        """ Prepare role persistent view """

        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            description='สวัสดีครับเพื่อน ๆ RU CS ทุกท่าน',
            colour=0xCCCCFF
        )

        await interaction.channel.send(embed=embed, view=RURolePersistentView())
        await interaction.followup.send('.', ephemeral=True)

    @app_commands.command()
    @app_commands.describe(amount='The amount of messages to delete', type='Type of messages to delete')
    # @app_commands.checks.has_permissions(manage_messages=True, read_message_history=True)
    # @app_commands.checks.bot_has_permissions(manage_messages=True, read_message_history=True)
    @app_commands.default_permissions(manage_messages=True, read_message_history=True)
    async def clear(
            self,
            interaction: Interaction,
            amount: int,
            type: Literal['BOT', 'Attachments', 'Embed'] = None) -> None:
        """Clear the messages of the channel"""
        await interaction.response.defer(ephemeral=True)

        if amount < 1:
            raise RuntimeError('Amount must be greater than 0')

        if amount > 100:
            raise RuntimeError('Amount must be less than 100')

        if type == 'BOT':
            deleted = await interaction.channel.purge(limit=amount, check=lambda m: m.author.bot)
        elif type == 'Attachments':
            deleted = await interaction.channel.purge(limit=amount, check=lambda m: m.attachments)
        elif type == 'Embed':
            deleted = await interaction.channel.purge(limit=amount, check=lambda m: m.embeds)
        else:
            deleted = await interaction.channel.purge(limit=amount)
        embed = discord.Embed(
            description=f"{interaction.channel.mention} : `{len(deleted)}` - messages were cleared",
            color=self.bot.theme
        )
        await interaction.followup.send(embed=embed)

    # ---------- Extension ---------- #

    @app_commands.command()
    @app_commands.describe(extension='extension name')
    @owner_only()
    async def load(self, interaction: Interaction, extension: str):
        """Loads an extension."""

        try:
            await self.bot.load_extension(f'{extension}')
        except commands.ExtensionAlreadyLoaded:
            raise app_commands.AppCommandError(f"The extension is already loaded.")
        except Exception as e:
            print(e)
            raise app_commands.AppCommandError('The extension load failed')
        else:
            embed = discord.Embed(description=f"Load : `{extension}`", color=0x8be28b)
            await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(extension='extension name')
    @owner_only()
    async def unload(self, interaction: Interaction, extension: str):
        """Unloads an extension."""

        try:
            await self.bot.unload_extension(f'{extension}')
        except commands.ExtensionNotLoaded:
            raise app_commands.AppCommandError(f"The extension is not loaded.")
        except Exception as e:
            print(e)
            raise app_commands.AppCommandError('The extension unload failed')
        else:
            embed = discord.Embed(description=f"Unload : `{extension}`", color=0x8be28b)
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name='reload')
    @app_commands.describe(extension='extension name')
    @owner_only()
    async def reload_(self, interaction: Interaction, extension: str):
        """Reloads an extension."""

        try:
            print(f"Reloading {extension}")
            await self.bot.reload_extension(f'{extension}')
        except commands.ExtensionNotLoaded:
            raise app_commands.AppCommandError(f'The extension was not loaded.')
        except commands.ExtensionNotFound:
            raise app_commands.AppCommandError(f'The Extension Not Found')
        except Exception as e:
            print(e)
            raise RuntimeError('The extension reload failed')
        else:
            embed = discord.Embed(description=f"Reload : `{extension}`", color=0x8be28b)
            await interaction.response.send_message(embed=embed)

    @load.autocomplete('extension')
    @unload.autocomplete('extension')
    @reload_.autocomplete('extension')
    async def tags_autocomplete(self, interaction: Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocomplete for extension names."""

        if interaction.user.id != self.bot.owner_id:
            return [
                app_commands.Choice(name='Only owner can use this command', value='Owner only can use this command')]

        cogs = [ext.lower() for ext in self.bot.initial_extensions]
        return [app_commands.Choice(name=cog.split('.')[1], value=cog) for cog in cogs]


async def setup(bot: RU_COMSCI_bot) -> None:
    await bot.add_cog(Admin(bot))
