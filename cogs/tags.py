from __future__ import annotations

import discord
import asyncpg
import datetime
from discord import app_commands
from discord.ext import commands

from typing import Optional, TypedDict, TYPE_CHECKING
from typing_extensions import Annotated

from utils.context import Context, GuildContext
from utils.paginator import SimplePages

if TYPE_CHECKING:
    from bot import RU_COMSCI_bot

class TagEntry(TypedDict):
    id: int
    name: str
    content: str


class TagPageEntry:
    __slots__ = ('id', 'name')

    def __init__(self, entry: TagEntry):
        self.id: int = entry['id']
        self.name: str = entry['name']

    def __str__(self) -> str:
        return f'{self.name} (ID: {self.id})'


class TagPageEntry:
    __slots__ = ('id', 'name')

    def __init__(self, entry: TagEntry):
        self.id: int = entry['id']
        self.name: str = entry['name']

    def __str__(self) -> str:
        return f'{self.name} (ID: {self.id})'


class TagPages(SimplePages):
    def __init__(self, entries: list[TagEntry], *, ctx: Context, per_page: int = 12):
        converted = [TagPageEntry(entry) for entry in entries]
        super().__init__(converted, per_page=per_page, ctx=ctx)


class TagName(commands.clean_content):
    def __init__(self, *, lower: bool = False):
        self.lower: bool = lower
        super().__init__()

    async def convert(self, ctx: Context, argument: str) -> str:
        converted = await super().convert(ctx, argument)
        lower = converted.lower().strip()

        if not lower:
            raise commands.BadArgument('ไม่มีชื่อแท็ก')

        if len(lower) > 100:
            raise commands.BadArgument('ชื่อแท็กมีความยาวสูงสุด 100 อักขระ')

        first_word, _, _ = lower.partition(' ')

        # get tag command.
        root: commands.GroupMixin = ctx.bot.get_command('tag')  # type: ignore
        if first_word in root.all_commands:
            raise commands.BadArgument('คุณไม่สามารถใช้ชื่อแท็กนี้ได้')

        return converted if not self.lower else lower


class TagCommands(commands.Cog, name='Tags'):
    """ Tag Commands """

    def __init__(self, bot: RU_COMSCI_bot) -> None:
        self.bot: RU_COMSCI_bot = bot
        self._reserved_tags_being_made: dict[int, set[str]] = {}

    def is_tag_being_made(self, guild_id: int, name: str) -> bool:
        try:
            being_made = self._reserved_tags_being_made[guild_id]
        except KeyError:
            return False
        else:
            return name.lower() in being_made

    async def get_tag(
            self,
            guild_id: Optional[int],
            name: str,
            *,
            connection: Optional[asyncpg.Pool | asyncpg.Connection] = None,
    ) -> TagEntry:
        def disambiguate(rows, query) -> str:
            if rows is None or len(rows) == 0:
                raise RuntimeError('ไม่พบแท็ก')

            names = '\n'.join(r['name'] for r in rows)
            raise RuntimeError(f'ไม่พบแท็ก คุณหมายถึง...\n`{names}`')

        con = connection or self.bot.pool

        query = """SELECT name, content FROM rucs_tags WHERE guild_id=$1 AND LOWER(name)=$2;"""
        row = await con.fetchrow(query, guild_id, name)
        if row is None:
            query = """SELECT     name
                       FROM       rucs_tags
                       WHERE      guild_id=$1 AND name % $2
                       ORDER BY   similarity(name, $2) DESC
                       LIMIT 3;
                    """
            return disambiguate(await con.fetch(query, guild_id, name), name)
        else:
            return row

    async def create_tag(self, ctx: GuildContext, name: str, content: str) -> None:

        is_already = await ctx.db.fetchrow(f'SELECT name from rucs_tags where LOWER(name) = $1 and guild_id = $2', name,
                                           ctx.guild.id)
        if is_already:
            return await ctx.send(f'แท็ก `{name}` มีอยู่แล้ว.')

        query = """INSERT INTO rucs_tags(name, content, owner_id, guild_id) VALUES ($1, $2, $3, $4);"""

        async with ctx.acquire():
            tr = ctx.db.transaction()  # type: ignore
            await tr.start()
            try:
                await ctx.db.execute(query, name, content, ctx.author.id, ctx.guild.id)
            except Exception as e:
                print(e)
                await tr.rollback()
                await ctx.send('ไม่สามารถสร้างแท็ก.')
            else:
                await tr.commit()
                await ctx.send(f'สร้างแท็ก `{name}` สำเร็จแล้ว.')

    @commands.hybrid_group(fallback='get')
    @app_commands.describe(name='แท็ก')
    @app_commands.guild_only()
    @commands.guild_only()
    async def tag(self, ctx: GuildContext, *, name: Annotated[str, TagName(lower=True)]) -> None:
        """ คำสั่งแท็ก """
        try:
            tag = await self.get_tag(ctx.guild.id, name, connection=ctx.db)
        except RuntimeError as e:
            return await ctx.send(str(e))

        await ctx.send(tag['content'], reference=ctx.replied_reference)

    @tag.command(aliases=['add', 'c'])
    @app_commands.describe(name='แท็ก', content='เนื้อหาของแท็ก')
    @app_commands.guild_only()
    @commands.guild_only()
    async def create(
            self, ctx: GuildContext, name: Annotated[str, TagName], *, content: Annotated[str, commands.clean_content]
    ) -> None:
        """ สร้างแท็ก """
        if len(content) > 2000:
            return await ctx.send('เนื้อหาแท็กมีความยาวสูงสุด 2,000 อักขระ')

        await self.create_tag(ctx, name, content)

    @tag.command()
    @app_commands.describe(name='แท็ก', content='เนื้อหาใหม่ของแท็ก')
    @app_commands.guild_only()
    @commands.guild_only()
    async def edit(
            self,
            ctx: GuildContext,
            name: Annotated[str, TagName(lower=True)],
            *,
            content: Annotated[str, commands.clean_content],
    ) -> None:
        """ แก้ไขแท็ก """
        query = "UPDATE rucs_tags SET content=$1 WHERE LOWER(name)=$2 AND guild_id=$3 AND owner_id=$4;"
        status = await ctx.db.execute(query, content, name, ctx.guild.id, ctx.author.id)

        if status[-1] == '0':
            await ctx.send('ไม่สามารถแก้ไขแท็กนั้นได้ คุณแน่ใจหรือว่ามันมีอยู่และคุณเป็นเจ้าของมัน?')
        else:
            await ctx.send('แก้ไขแท็กเรียบร้อยแล้ว.')

    @tag.command(aliases=['delete'])
    @app_commands.describe(name='แท็ก')
    @app_commands.guild_only()
    @commands.guild_only()
    async def remove(self, ctx: GuildContext, *, name: Annotated[str, TagName(lower=True)]) -> None:
        """ ลบแท็ก """

        bypass_owner_check = ctx.author.id == self.bot.owner_id or ctx.author.guild_permissions.manage_messages
        clause = 'LOWER(name)=$1 AND guild_id=$2'

        if bypass_owner_check:
            args = [name, ctx.guild.id]
        else:
            args = [name, ctx.guild.id, ctx.author.id]
            clause = f'{clause} AND owner_id=$3'

        query = f'DELETE FROM rucs_tags WHERE {clause} RETURNING name;'
        deleted = await ctx.db.fetchrow(query, *args)

        if deleted is None:
            await ctx.send('ไม่สามารถลบแท็ก ไม่มีอยู่จริงหรือคุณไม่ได้รับอนุญาตให้ทำเช่นนั้น')
            return

        await ctx.send(f'แท็ก `{deleted[0]}` ถูกลบเรียบร้อยแล้ว')

    @tag.command()
    @app_commands.describe(old_name='แท็ก', new_name='ชื่อใหม่ของแท็ก')
    @app_commands.guild_only()
    @commands.guild_only()
    async def rename(self, ctx: GuildContext, old_name: Annotated[str, TagName], *,
                     new_name: Annotated[str, TagName]) -> None:
        """ เปลี่ยนชื่อแท็ก """
        if old_name.lower() == new_name.lower():
            return await ctx.send('ไม่สามารถเปลี่ยนชื่อแท็กให้เหมือนกันได้')

        bypass_owner_check = ctx.author.id == self.bot.owner_id or ctx.author.guild_permissions.manage_messages
        clause = 'LOWER(name)=$1 AND guild_id=$2'

        if bypass_owner_check:
            args = [old_name, ctx.guild.id]
        else:
            args = [old_name, ctx.guild.id, ctx.author.id]
            clause = f'{clause} AND owner_id=$3'

        query = f'SELECT id FROM rucs_tags WHERE {clause};'
        selected = await ctx.db.fetchrow(query, *args)
        if selected is None:
            return await ctx.send('ไม่สามารถเปลี่ยนชื่อแท็กได้ แท็กไม่มีอยู่จริงหรือคุณไม่ได้รับอนุญาต')

        # check if tag exists
        query = f'SELECT name FROM rucs_tags WHERE name = $1;'
        exists = await ctx.db.fetchrow(query, new_name.lower())
        if exists is not None:
            if exists['name'].lower() == new_name.lower():
                return await ctx.send(f'แท็ก `{new_name}` มีอยู่แล้ว กรุณาเลือกชื่อใหม่')

        args.append(new_name)
        query = f'UPDATE rucs_tags SET name=${len(args)} WHERE {clause};'
        await ctx.db.execute(query, *args)
        await ctx.send(f'แท็ก `{old_name}` ถูกเปลี่ยนชื่อเป็น `{new_name}` เรียบร้อยแล้ว')

    @tag.command(name='list')
    @app_commands.describe(member="ผู้ใช้ที่ต้องการดูแท็ก")
    @app_commands.guild_only()
    @commands.guild_only()
    async def _list(self, ctx: GuildContext, member: Optional[discord.Member] = None) -> None:
        """ ดูแท็กทั่งหมด หรือ ดูแท็กของผู้ใช้ที่ระบุ """

        clause = 'guild_id=$1'
        args = [ctx.guild.id]
        if member is not None:
            clause = f'{clause} AND owner_id=$2'
            args = [ctx.guild.id, member.id]

        query = f"SELECT name, id FROM rucs_tags WHERE {clause} ORDER BY name;"

        rows = await ctx.db.fetch(query, *args)
        await ctx.release()

        if rows:
            p = TagPages(entries=rows, ctx=ctx)
            p.embed.color = self.bot.theme
            if member is not None:
                p.embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            await p.start()
        else:
            await ctx.send(f'ไม่พบแท็กใดๆ')

    @tag.command()
    @app_commands.describe(query="คำค้นหาแท็ก")
    @app_commands.guild_only()
    @commands.guild_only()
    async def search(self, ctx: GuildContext, *, query: Annotated[str, commands.clean_content]) -> None:
        """ ค้นหาแท็ก """
        if len(query) < 3:
            return await ctx.send('ข้อความค้นหาต้องมีอย่าง 3 อักขระ')

        sql = """SELECT name, id
                 FROM rucs_tags
                 WHERE guild_id=$1 AND name % $2
                 ORDER BY similarity(name, $2) DESC
                 LIMIT 100;
              """

        results = await ctx.db.fetch(sql, ctx.guild.id, query)

        if results:
            p = TagPages(entries=results, per_page=20, ctx=ctx)
            p.embed.color = self.bot.theme
            await ctx.release()
            await p.start()
        else:
            await ctx.send('ไม่พบแท็ก')

    @tag.command(aliases=['owner'])
    @app_commands.describe(name='ชื่อแท็ก')
    @app_commands.guild_only()
    @commands.guild_only()
    async def info(self, ctx: GuildContext, *, name: Annotated[str, TagName(lower=True)]) -> None:
        """ ดูข้อมูลแท็ก """

        query = """SELECT * FROM rucs_tags WHERE LOWER(name)=$1 AND guild_id=$2"""

        record = await ctx.db.fetchrow(query, name, ctx.guild.id)
        if record is None:
            return await ctx.send('ไม่พบแท็กนี้')

        embed = discord.Embed(colour=self.bot.theme)

        owner_id = record['owner_id']
        embed.title = record['name']
        embed.timestamp = record['created_at'].replace(tzinfo=datetime.timezone.utc)
        embed.set_footer(text='แท็กถูกสร้างเมื่อ')

        user = self.bot.get_user(owner_id) or (await self.bot.fetch_user(owner_id))
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)

        # owner
        embed.add_field(name='เจ้าของ', value=f'<@{owner_id}>')
        await ctx.send(embed=embed)


async def setup(bot: RU_COMSCI_bot) -> None:
    await bot.add_cog(TagCommands(bot))
