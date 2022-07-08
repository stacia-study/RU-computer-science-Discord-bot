from __future__ import annotations

import discord
import traceback
from difflib import get_close_matches
from discord import Interaction
from discord.ext import commands
from discord.app_commands import (
    AppCommandError,
    CommandInvokeError,
    CommandNotFound,
    MissingPermissions,
    BotMissingPermissions,
    CheckFailure,
    CommandSignatureMismatch,
    CommandOnCooldown
)
from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from bot import RU_COMSCI_bot


class ErrorHandler(commands.Cog):
    """Error handler"""

    def __init__(self, bot: RU_COMSCI_bot) -> None:
        self.bot: RU_COMSCI_bot = bot
        self.bot.tree.on_error = self.on_app_command_error

    async def on_app_command_error(self, interaction: Interaction, error: AppCommandError):
        """ Handles errors for all application commands associated with this CommandTree."""

        traceback.print_exception(type(error), error, error.__traceback__)

        error_unknown = "An unknown error occurred, sorry"
        if isinstance(error, CommandInvokeError) and not isinstance(error, (
        KeyError, ValueError, TypeError, IndexError, AttributeError)):
            error = error.original
        elif isinstance(error, Union[CommandNotFound, MissingPermissions, BotMissingPermissions]):
            error = error
        elif isinstance(error, CommandOnCooldown):
            error = error
        elif isinstance(error, Union[CommandSignatureMismatch, CommandNotFound]):
            error = "Sorry, but this command seems to be unavailable! Please try again later..."
        elif isinstance(error, CheckFailure):
            error = "You can't use this command."
        else:
            error = error_unknown
            traceback.print_exception(type(error), error, error.__traceback__)

        if interaction is not None:

            error_content = f'{str(error)[:1950]}' if len(str(error)) < 100 else error_unknown
            embed = discord.Embed(description=error_content, color=0xfe676e)
            if interaction.response.is_done():
                return await interaction.followup.send(embed=embed, ephemeral=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:

        embed = discord.Embed(color=self.bot.theme)

        if isinstance(error, commands.CommandNotFound):
            command_names = [str(x) for x in ctx.bot.commands]
            matches = get_close_matches(ctx.invoked_with, command_names)
            if matches:
                matches = "\n".join(matches)
                cm_error = f"ไม่พบคำสั่งนั้น คุณหมายถึง...\n`{matches}`"
            else:
                return
        elif isinstance(error, commands.UserInputError):
            cm_error = f"{error}"
        elif isinstance(error, commands.DisabledCommand):
            cm_error = f"คำสั่งปิดใช้งานอยู่"
        elif isinstance(error, commands.MissingPermissions):
            missing = [perm.replace("_", " ").replace("guild", "server").replace("moderate", "timeout").title() for perm
                       in error.missing_permissions]
            if len(missing) > 2:
                fmt = "{}, and {}".format(", ".join(missing[:-1]), missing[-1])
            else:
                fmt = " and ".join(missing)
            if len(missing) < 2:
                cm_error = f"คุณต้องได้รับอนุญาต ``{fmt}`` เพื่อรันคำสั่ง"
            else:
                cm_error = f"คุณไม่ได้รับอนุญาต ``{fmt}`` เพื่อรันคำสั่ง"
        elif isinstance(error, commands.NoPrivateMessage):
            cm_error = f"ไม่สามารถใช้คำสั่งในแชทส่วนตัว"
        elif isinstance(error, commands.CheckFailure):
            cm_error = f"คุณไม่สามารถใช้คำสั่งนี้ได้"
        else:
            cm_error = f"เกิดข้อผิดพลาดที่ไม่ทราบสาเหตุ ขออภัย"
            print(error)
        embed.description = cm_error
        await ctx.send(embed=embed, delete_after=30, ephemeral=True)


async def setup(bot: RU_COMSCI_bot) -> None:
    await bot.add_cog(ErrorHandler(bot))
