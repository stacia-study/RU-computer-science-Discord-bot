import discord
from discord import ui
from enum import Enum


class RoleID(Enum):
    student = 994917404859711528
    teacher = 994917240711413831
    other = 994917733030436954

class RURolePersistentView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='อาจารย์', emoji='👩‍🏫', style=discord.ButtonStyle.blurple, custom_id='persistent_view:ru_cs_teacher')
    async def ru_cs_teacher(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        role = interaction.guild.get_role(int(RoleID.teacher.value))
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            return await interaction.followup.send(
                f'{interaction.user.mention} ได้รับยศ {role.mention}',
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions(users=False, roles=False)
            )
        await interaction.user.remove_roles(role)

    @discord.ui.button(label='นักศึกษา', emoji='👩‍🎓', style=discord.ButtonStyle.blurple, custom_id='persistent_view:ru_cs_64')
    async def student(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        role = interaction.guild.get_role(int(RoleID.student.value))
        print(role)
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            return await interaction.followup.send(
                f'{interaction.user.mention} ได้รับยศ {role.mention}',
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions(users=False, roles=False)
            )
        await interaction.user.remove_roles(role)

    @discord.ui.button(label='อื่นๆ', emoji='<:member:904565339835232276>', style=discord.ButtonStyle.blurple, custom_id='persistent_view:ru_cs_other')
    async def ru_cs_other(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        role = interaction.guild.get_role(int(RoleID.other.value))
        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            return await interaction.followup.send(
                f'{interaction.user.mention} ได้รับยศ {role.mention}',
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions(users=False, roles=False)
            )
        await interaction.user.remove_roles(role)
