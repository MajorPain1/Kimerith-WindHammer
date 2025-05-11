from typing import List, Optional, Literal
from fuzzywuzzy import process, fuzz
from operator import itemgetter
import os
from pathlib import Path

import discord
from discord import app_commands, PartialMessageable, DMChannel
from discord.ext import commands
from loguru import logger

from ..database import StatObject, _make_placeholders, sql_chunked
from .. import TheBot, database, emojis
from ..menus import ItemView


FIND_MOB_QUERY = """
SELECT * FROM mobs
INNER JOIN locale_en ON locale_en.id == mobs.name
WHERE locale_en.data == ? COLLATE NOCASE
"""

FIND_MOB_WITH_FILTER_QUERY = """
SELECT * FROM mobs
INNER JOIN locale_en ON locale_en.id == mobs.name
WHERE locale_en.data COLLATE NOCASE IN ({placeholders})
AND (? = 'Any' OR mobs.primary_school = ?)
AND (? = 'Any' OR mobs.title = ?)
AND (? = -1 OR mobs.rank = ?)
COLLATE NOCASE
"""


FIND_OBJECT_NAME_QUERY = """
SELECT * FROM mobs
INNER JOIN locale_en ON locale_en.id == mobs.name
WHERE mobs.real_name == ? COLLATE NOCASE
"""

class Mobs(commands.GroupCog, name="mob"):
    def __init__(self, bot: TheBot):
        self.bot = bot

    async def fetch_mob(self, name: str) -> List[tuple]:
        async with self.bot.db.execute(FIND_MOB_QUERY, (name,)) as cursor:
            return await cursor.fetchall()
    
    async def fetch_object_name(self, name: str) -> List[tuple]:
        name_bytes = name.encode('utf-8')
        async with self.bot.db.execute(FIND_OBJECT_NAME_QUERY, (name_bytes,)) as cursor:
            return await cursor.fetchall()

    async def fetch_mobs_with_filter(self, mobs, school: Optional[str] = "Any", kind: Optional[str] = "Any", rank: Optional[int] = -1, return_row=False):
        if isinstance(mobs, str):
            mobs = [mobs]

        results = []
        
        school_val = (database._SCHOOLS_STR.index(school) + 2) if school != "Any" else None

        for chunk in sql_chunked(mobs, 900):  # Stay under SQLite's limit
            placeholders = _make_placeholders(len(chunk))
            query = FIND_MOB_WITH_FILTER_QUERY.format(placeholders=placeholders)

            args = (
                *chunk,
                school, school_val,
                kind, kind,
                rank, rank
            )

            async with self.bot.db.execute(query, args) as cursor:
                rows = await cursor.fetchall()

            if return_row:
                results.extend(rows)
            else:
                results.extend(row[-1] for row in rows)

        return results

    async def fetch_mob_stats(self, mob: int) -> List[StatObject]:
        stats = []

        async with self.bot.db.execute(
            "SELECT * FROM mob_stats WHERE mob == ?", (mob,)
        ) as cursor:
            async for row in cursor:
                a = row[3]
                b = row[4]

                match row[2]:
                    # Regular stat
                    case 1:
                        order, stat = database.translate_stat(a)
                        stats.append(StatObject(order, b, stat))

                    # Starting pips
                    case 2:
                        if a != 0:
                            stats.append(StatObject(1320, a, f"{emojis.PIP}"))
                        if b != 0:
                            stats.append(StatObject(1330, b, f"{emojis.POWER_PIP}"))

                    # Speed bonus
                    case 5:
                        stats.append(StatObject(1340, a, f"{emojis.SPEED}"))

        stats = sorted(stats, key=lambda stat: stat.order)

        return stats
    
    async def fetch_mob_items(self, mob: int) -> List[str]:
        items = []

        async with self.bot.db.execute(
            "SELECT * FROM mob_items WHERE mob == ?", (mob,)
        ) as cursor:
            async for row in cursor:
                items.append(row[2]) # item id

        return items
    
    async def fetch_item_names(self, ids: List[str]) -> List[str]:
        items = []
        placeholders = ','.join(['?'] * len(ids))
        
        async with self.bot.db.execute(
            f"SELECT * FROM items WHERE id IN ({placeholders})", ids
        ) as cursor:
            async for row in cursor:
                items.append(row[2])
        
        return items
        
        
    
    async def fetch_mob_deck(self, item_list: List[str], mob_real_name: str) -> List[tuple]:
        deck_spells = []
        placeholders = ','.join(['?'] * len(item_list))
        async with self.bot.db.execute(
            f"SELECT * FROM deck WHERE name IN ({placeholders})", item_list
        ) as cursor:
            async for row in cursor:
                deck_spells.append((row[2], row[3]))
        
        if len(deck_spells) == 0:
            async with self.bot.deck_db.execute(
                f"SELECT * FROM deck WHERE name IN ({placeholders})", item_list
            ) as cursor:
                async for row in cursor:
                    deck_spells.append((row[2], row[3]))
        
        async with self.bot.db.execute(
            f"SELECT * FROM deck WHERE name == ?", (mob_real_name,)
        ) as cursor:
            async for row in cursor:
                deck_spells.append((row[2], row[3]))
        
        return deck_spells


    async def build_mob_embed(self, row) -> discord.Embed:
        mob_id = row[0]
        real_name: str = row[2].decode("utf-8") 
        image_file = row[3].decode("utf-8")
        title = row[4]
        rank = row[5]
        hp = row[6]
        school = row[7]
        secondary_school = row[8]
        stunnable = row[9]
        max_shadow = row[10]
        has_cheats = row[11]
        intelligence = row[12]
        selfishness = row[13]
        aggressiveness = row[14]
        monstro = database.MonstrologyKind(row[15])
        mob_name = row[17]

        ai = [f"Intelligence {intelligence}", f"Selfishness {selfishness}", f"Aggressiveness {aggressiveness}"]

        stats = await self.fetch_mob_stats(mob_id)
        items = await self.fetch_mob_items(mob_id)
        await database.sum_stats(self.bot.db, stats, items)

        stats = sorted(stats, key=lambda stat: stat.order)
        _return_stats = []
        for stat in stats:
            if "polymorph" in real_name.lower():
                stat.value = int(stat.value / 2)
            _return_stats.append(stat.to_string())

        stats = _return_stats

        flags = []
        if secondary_school:
            flags.append(f"Secondary School {database.translate_school(secondary_school)}")
        if bool(has_cheats):
            flags.append(f"This {title} Mob Cheats!")
        if max_shadow > 0:
            stats.append(f"Max {max_shadow} {emojis.SHADOW_PIP}")
        if not stunnable:
            flags.append(f"Stunnable and Beguilable")
        
        extracts = database.get_monstrology_string(monstro)

        embed = (
            discord.Embed(
                color=database.make_school_color(school),
                description="\n".join(stats) or "\u200b",
            )
            .set_author(name=f"{mob_name}\n({real_name}: {mob_id})\nHP {hp}\nRank {rank} {title}", icon_url=database.translate_school(school).url)
            .add_field(name="AI", value="\n".join(ai))
        )

        if flags:
            embed.add_field(name="Flags", value="\n".join(flags))

        if extracts:
            embed.add_field(name="Extracts", value="\n".join(extracts))

        discord_file = None
        if image_file:
            try:
                image_name = (image_file.split("|")[-1]).split(".")[0]
                png_file = f"{image_name}.png"
                png_name = png_file.replace(" ", "")
                png_name = os.path.basename(png_name)
                file_path = Path("PNG_Images") / png_name
                discord_file = discord.File(file_path, filename=png_name)
                embed.set_thumbnail(url=f"attachment://{png_name}")
            except:
                pass

        return embed, discord_file

    async def build_deck_embed(self, row) -> discord.Embed:
        mob_id = row[0]
        real_name = row[2]
        decoded_name = real_name.decode("utf-8")
        image_file = row[3].decode("utf-8")
        title = row[4]
        rank = row[5]
        hp = row[6]
        school = row[7]
        secondary_school = row[8]
        stunnable = row[9]
        max_shadow = row[10]
        has_cheats = row[11]
        intelligence = row[12]
        selfishness = row[13]
        aggressiveness = row[14]
        monstro = database.MonstrologyKind(row[15])
        mob_name = row[17]

        items = await self.fetch_mob_items(mob_id)
        item_names = await self.fetch_item_names(items)
        deck_spells = await self.fetch_mob_deck(item_names, real_name)
        
        formatted_spells = []
        for spell in deck_spells:
            spell_name = spell[0].decode("utf-8")
            formatted_spells.append(f"{spell_name} x{spell[1]}")
        

        embed = (
            discord.Embed(
                color=database.make_school_color(school),
                description="**Spell Deck**\n" + "\n".join(formatted_spells) or "\u200b",
            )
            .set_author(name=f"{mob_name}\n({decoded_name}: {mob_id})", icon_url=database.translate_school(school).url)
        )
        

        discord_file = None
        if image_file:
            try:
                image_name = (image_file.split("|")[-1]).split(".")[0]
                png_file = f"{image_name}.png"
                png_name = png_file.replace(" ", "")
                png_name = os.path.basename(png_name)
                file_path = Path("PNG_Images") / png_name
                discord_file = discord.File(file_path, filename=png_name)
                embed.set_thumbnail(url=f"attachment://{png_name}")
            except:
                pass

        return embed, discord_file
    
    async def build_calc_embed(self, row, school, base, damage, pierce, critical, buffs, pvp):
        mob_id = row[0]
        real_name: str = row[2].decode("utf-8") 
        image_file = row[3].decode("utf-8")
        hp = row[6]
        mob_school = row[7]
        mob_name = row[17]
        
        school_int = database._SCHOOLS_STR.index(school) + 2
        school_emoji = database.translate_school(school_int)
        
        buffs_as_modifiers = database.translate_buffs(buffs)
        
        stats = await self.fetch_mob_stats(mob_id)
        items = await self.fetch_mob_items(mob_id)
        await database.sum_stats(self.bot.db, stats, items)
        
        mob_buffs = []
        mob_block = 0
        for stat in stats:
            if stat.string == f" {school_emoji}{database.RESIST}" or stat.string == f" {database.RESIST}":
                mob_buffs.append(stat.value)
                
            elif stat.string == f" {school_emoji}{database.BLOCK} Rating" or stat.string == f" {database.BLOCK} Rating":
                mob_block += stat.value
        
        mob_buff = sum(mob_buffs)
        if mob_buff < 0:
            buffs_as_modifiers.append(database.Buff(float(-mob_buff), False))
        elif mob_buff > 0:
            buffs_as_modifiers.append(database.Buff(float(-mob_buff), True))
            
        no_crit, crit = database.calc_damage(base, damage, pierce, critical, buffs_as_modifiers, mob_block, pvp)
        curved_damage = round((database.pve_damage_curve(damage) * 100) - 100, 2)
        curved_str = f" ({curved_damage}% {school_emoji}{database.DAMAGE})"
        show_curved = int(float(damage) != curved_damage)
        embed = (
            discord.Embed(
                color=database.make_school_color(mob_school),
                description=f"{base}{database.DAMAGE} Base\n\nStats:\n{damage}% {school_emoji}{database.DAMAGE}{curved_str*show_curved}\n{pierce}% {school_emoji}{database.PIERCE}\n{critical} {school_emoji}{database.CRIT}\n{mob_buff}% {school_emoji}{database.RESIST}\n{mob_block} {school_emoji}{database.BLOCK}\n\nBuffs: {buffs}"
            )
            .set_author(name=f"Damage Calc on {mob_name}\n({real_name}: {mob_id})\nHP {hp}", icon_url=database.translate_school(mob_school).url)
            .add_field(name="No Crit Damage", value=f"{no_crit:,}{database.DAMAGE}")
            .add_field(name="Crit Damage", value=f"{crit:,}{database.DAMAGE}")
        )
        
        discord_file = None
        if image_file:
            try:
                image_name = (image_file.split("|")[-1]).split(".")[0]
                png_file = f"{image_name}.png"
                png_name = png_file.replace(" ", "")
                png_name = os.path.basename(png_name)
                file_path = Path("PNG_Images") / png_name
                discord_file = discord.File(file_path, filename=png_name)
                embed.set_thumbnail(url=f"attachment://{png_name}")
            except:
                pass

        return embed, discord_file


    @app_commands.command(name="find", description="Finds a Wizard101 mob by name")
    @app_commands.describe(name="The name of the mob to search for")
    async def find(
        self, 
        interaction: discord.Interaction, 
        name: str,
        school: Optional[Literal["Any", "Fire", "Ice", "Storm", "Myth", "Life", "Death", "Balance", "Star", "Sun", "Moon", "Shadow"]] = "Any",
        kind: Optional[Literal["Any", "Easy", "Normal", "Elite", "Boss"]] = "Any",
        rank: Optional[int] = -1,
        use_object_name: Optional[bool] = False,
    ):
        await interaction.response.defer()
        if type(interaction.channel) is DMChannel or type(interaction.channel) is PartialMessageable:
            logger.info("{} requested mob '{}'", interaction.user.name, name)
        else:
            logger.info("{} requested mob '{}' in channel #{} of {}", interaction.user.name, name, interaction.channel.name, interaction.guild.name)

        if use_object_name:
            rows = await self.fetch_object_name(name)
            if not rows:
                embed = discord.Embed(description=f"No mobs with object name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                await interaction.followup.send(embed=embed)
        else:
            rows = await self.fetch_mobs_with_filter(name, school, kind, rank, return_row=True)
            if not rows:
                filtered_rows = await self.fetch_mobs_with_filter(self.bot.mob_list, school, kind, rank, return_row=True)
                closest_rows = [(row, fuzz.token_set_ratio(name, row[-1]) + fuzz.ratio(name, row[-1])) for row in filtered_rows]
                closest_rows = sorted(closest_rows, key=lambda x: x[1], reverse=True)
                closest_rows = list(zip(*closest_rows))[0]

                rows = await self.fetch_mobs_with_filter(closest_rows[0][-1], school, kind, rank, return_row=True)
                if rows:
                    logger.info("Failed to find '{}' instead searching for {}", name, closest_rows[0][-1])

        if rows:
            embeds = [await self.build_mob_embed(row) for row in rows]
            sorted_embeds = sorted(embeds, key=lambda embed: embed[0].author.name)
            unzipped_embeds, unzipped_images = list(zip(*sorted_embeds))
            view = ItemView(unzipped_embeds, files=unzipped_images)
            await view.start(interaction)
        elif not use_object_name:
            logger.info("Failed to find '{}'", name)
            embed = discord.Embed(description=f"No mobs with name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="deck", description="Finds a Wizard101 mob deck by name")
    @app_commands.describe(name="The name of the mob to search for")
    async def deck(
        self, 
        interaction: discord.Interaction, 
        name: str,
        school: Optional[Literal["Any", "Fire", "Ice", "Storm", "Myth", "Life", "Death", "Balance", "Star", "Sun", "Moon", "Shadow"]] = "Any",
        kind: Optional[Literal["Any", "Easy", "Normal", "Elite", "Boss"]] = "Any",
        rank: Optional[int] = -1,
        use_object_name: Optional[bool] = False,
    ):
        await interaction.response.defer()
        if type(interaction.channel) is DMChannel or type(interaction.channel) is PartialMessageable:
            logger.info("{} requested mob deck '{}'", interaction.user.name, name)
        else:
            logger.info("{} requested mob deck '{}' in channel #{} of {}", interaction.user.name, name, interaction.channel.name, interaction.guild.name)

        if use_object_name:
            rows = await self.fetch_object_name(name)
            if not rows:
                embed = discord.Embed(description=f"No mobs with object name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                await interaction.followup.send(embed=embed)
        else:
            rows = await self.fetch_mobs_with_filter(name, school, kind, rank, return_row=True)
            if not rows:
                filtered_rows = await self.fetch_mobs_with_filter(self.bot.mob_list, school, kind, rank, return_row=True)
                closest_rows = [(row, fuzz.token_set_ratio(name, row[-1]) + fuzz.ratio(name, row[-1])) for row in filtered_rows]
                closest_rows = sorted(closest_rows, key=lambda x: x[1], reverse=True)
                closest_rows = list(zip(*closest_rows))[0]

                rows = await self.fetch_mobs_with_filter(closest_rows[0][-1], school, kind, rank, return_row=True)
                if rows:
                    logger.info("Failed to find '{}' instead searching for {}", name, closest_rows[0][-1])

        if rows:
            embeds = [await self.build_deck_embed(row) for row in rows]
            sorted_embeds = sorted(embeds, key=lambda embed: embed[0].author.name)
            unzipped_embeds, unzipped_images = list(zip(*sorted_embeds))
            view = ItemView(unzipped_embeds, files=unzipped_images)
            await view.start(interaction)
        elif not use_object_name:
            logger.info("Failed to find '{}'", name)
            embed = discord.Embed(description=f"No mobs with name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="list", description="Finds a list of mob names that contain the string")
    @app_commands.describe(name="The name of the mobs to search for")
    async def list_names(
        self, 
        interaction: discord.Interaction, 
        name: str,
        school: Optional[Literal["Any", "Fire", "Ice", "Storm", "Myth", "Life", "Death", "Balance", "Star", "Sun", "Moon", "Shadow"]] = "Any",
        kind: Optional[Literal["Any", "Easy", "Normal", "Elite", "Boss"]] = "Any",
        rank: Optional[int] = -1,
    ):
        await interaction.response.defer()
        if type(interaction.channel) is DMChannel or type(interaction.channel) is PartialMessageable:
            logger.info("{} searched for mobs that contain '{}'", interaction.user.name, name)
        else:
            logger.info("{} searched for mobs that contain '{}' in channel #{} of {}", interaction.user.name, name, interaction.channel.name, interaction.guild.name)

        mobs_containing_name = []
        for mob in self.bot.mob_list:
            mob: str

            if name == '*' or name.lower() in mob.lower():
                mobs_containing_name.append(mob)

        no_duplicate_mobs = [*set(mobs_containing_name)]
        filtered_mobs = await self.fetch_mobs_with_filter(mobs=no_duplicate_mobs, school=school, kind=kind, rank=rank)
        no_no_duplicate_mobs = [*set(filtered_mobs)]
        alphabetic_mobs = sorted(no_no_duplicate_mobs)

        if len(alphabetic_mobs) > 0:
            chunks = [alphabetic_mobs[i:i+15] for i in range(0, len(alphabetic_mobs), 15)]
            mob_embeds = []
            for mob_chunk in chunks:
                embed = (
                    discord.Embed(
                        description="\n".join(mob_chunk) or "\u200b",
                    )
                    .set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                )
                mob_embeds.append(embed)

            view = ItemView(mob_embeds)
            await view.start(interaction)

        else:
            embed = discord.Embed(description=f"Unable to find {name}.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="calc", description="Calcs damage against a specific mob")
    @app_commands.describe(name="The name of the mobs to search for", buffs="Your buffs separated by a space (use a \"P\" prefix to denote pierce) EX: 35 35 40 20P -50P", damage="Input your pre-curved damage if you are in PvE")
    async def calc(
        self,
        interaction: discord.Interaction,
        name: str,
        school: Literal["Fire", "Ice", "Storm", "Myth", "Life", "Death", "Balance", "Star", "Sun", "Moon", "Shadow"],
        base: int,
        damage: int,
        pierce: int,
        critical: int,
        use_object_name: Optional[bool] = False,
        buffs: Optional[str] = "",
        pvp: Optional[bool] = True,
    ):
        await interaction.response.defer()
        if type(interaction.channel) is DMChannel or type(interaction.channel) is PartialMessageable:
            logger.info("{} requested calc on mob '{}'", interaction.user.name, name)
        else:
            logger.info("{} requested calc on mob '{}' in channel #{} of {}", interaction.user.name, name, interaction.channel.name, interaction.guild.name)

        if use_object_name:
            rows = await self.fetch_object_name(name)
            if not rows:
                embed = discord.Embed(description=f"No mobs with object name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                await interaction.followup.send(embed=embed)
        else:
            rows = await self.fetch_mob(name)
            if not rows:
                closest_names = [(string, fuzz.token_set_ratio(name, string) + fuzz.ratio(name, string)) for string in self.bot.mob_list]
                closest_names = sorted(closest_names, key=lambda x: x[1], reverse=True)
                closest_names = list(zip(*closest_names))[0]

                rows = await self.fetch_mob(closest_names[0])
                if rows:
                    logger.info("Failed to find '{}' instead searching for {}", name, closest_names[0])
        
        if rows:
            embeds = [await self.build_calc_embed(row, school, base, damage, pierce, critical, buffs, pvp) for row in rows]
            sorted_embeds = sorted(embeds, key=lambda embed: embed[0].author.name)
            unzipped_embeds, unzipped_images = list(zip(*sorted_embeds))
            view = ItemView(unzipped_embeds, files=unzipped_images)
            await view.start(interaction)
        elif not use_object_name:
            logger.info("Failed to find '{}'", name)
            embed = discord.Embed(description=f"No mobs with name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
            await interaction.followup.send(embed=embed)



async def setup(bot: TheBot):
    await bot.add_cog(Mobs(bot))
