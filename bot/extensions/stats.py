from typing import List, Optional, Literal
from fuzzywuzzy import process, fuzz
from operator import itemgetter
from random import choice

import discord
from discord import app_commands, PartialMessageable
from discord.ext import commands
from loguru import logger

from ..database import StatObject
from .. import TheBot, database, emojis
from ..menus import ItemView


FIND_ITEM_QUERY = """
SELECT * FROM items
INNER JOIN locale_en ON locale_en.id == items.name
WHERE locale_en.data == ? COLLATE NOCASE
"""

FIND_ITEM_OBJECT_NAME_QUERY = """
SELECT * FROM items
INNER JOIN locale_en ON locale_en.id == items.name
WHERE items.real_name == ? COLLATE NOCASE
"""

FIND_ITEMCARD_OBJECT_NAME_QUERY = """
SELECT * FROM spells
WHERE spells.template_id == ? COLLATE NOCASE
"""

FIND_SET_QUERY = """
SELECT * FROM set_bonuses
"""

SET_BONUS_NAME_QUERY = """
SELECT locale_en.data FROM set_bonuses
INNER JOIN locale_en ON locale_en.id == set_bonuses.name
WHERE set_bonuses.id == ?
"""

SPELL_NAME_ID_QUERY = """
SELECT locale_en.data FROM spells
INNER JOIN locale_en ON locale_en.id == spells.name
WHERE spells.template_id == ?
"""

FIND_ITEMS_WITH_FILTER_QUERY = """
SELECT * FROM items
INNER JOIN locale_en ON locale_en.id == items.name
WHERE locale_en.data COLLATE NOCASE IN ({placeholders})
AND (? = 'Any' OR items.equip_school = ?)
AND (? = 'Any' OR items.kind = ?)
AND (? = -1 OR items.equip_level = ?)
COLLATE NOCASE
"""


class Stats(commands.GroupCog, name="item"):
    def __init__(self, bot: TheBot):
        self.bot = bot

    async def fetch_item(self, name: str) -> List[tuple]:
        async with self.bot.db.execute(FIND_ITEM_QUERY, (name,)) as cursor:
            return await cursor.fetchall()
        
    async def fetch_object_name(self, name: str) -> List[tuple]:
        name_bytes = name.encode('utf-8')
        async with self.bot.db.execute(FIND_ITEM_OBJECT_NAME_QUERY, (name_bytes,)) as cursor:
            return await cursor.fetchall()
        
    async def fetch_itemcard_object_name(self, id: str) -> List[tuple]:
        async with self.bot.db.execute(FIND_ITEMCARD_OBJECT_NAME_QUERY, (id,)) as cursor:
            return await cursor.fetchall()
        
    async def fetch_set_bonus_name(self, set_id: int) -> Optional[tuple]:
        async with self.bot.db.execute(SET_BONUS_NAME_QUERY, (set_id,)) as cursor:
            return (await cursor.fetchone())[0]


    async def fetch_items_with_filter(self, items, school: Optional[str] = "Any", kind: Optional[str] = "Any", level: Optional[int] = -1, return_row=False):
        if isinstance(items, str):
            items = [items]

        results = []
        
        school_val = (database._SCHOOLS_STR.index(school) + 2) if school != "Any" else None
        kind_val = (1 << database._ITEMS_STR.index(kind)) if kind != "Any" else None

        for chunk in database.sql_chunked(items, 900):  # Stay under SQLite's limit
            placeholders = database._make_placeholders(len(chunk))
            query = FIND_ITEMS_WITH_FILTER_QUERY.format(placeholders=placeholders)

            args = (
                *chunk,
                school, school_val,
                kind, kind_val,
                level, level
            )

            async with self.bot.db.execute(query, args) as cursor:
                rows = await cursor.fetchall()

            if return_row:
                results.extend(rows)
            else:
                results.extend(row[-1] for row in rows)

        return results


    async def fetch_item_stats(self, item: int) -> List[str]:
        stats = []

        async with self.bot.db.execute(
            "SELECT * FROM item_stats WHERE item == ?", (item,)
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
                            stats.append(StatObject(1320, a, f" {emojis.PIP}"))
                        if b != 0:
                            stats.append(StatObject(1330, b, f" {emojis.POWER_PIP}"))
                    
                    # Itemcards
                    case 3:
                        async with self.bot.db.execute(SPELL_NAME_ID_QUERY, (a,)) as cursor:
                            card_name = (await cursor.fetchone())[0]

                        object_name = (await self.fetch_itemcard_object_name(a))[0][3]

                        copies = b
                        stats.append(StatObject(1500, 0, f"Gives {copies} {card_name} ({object_name.decode()})"))
                    
                    # Maycasts
                    case 4:
                        async with self.bot.db.execute(SPELL_NAME_ID_QUERY, (a,)) as cursor:
                            card_name = (await cursor.fetchone())[0]

                        object_name = (await self.fetch_itemcard_object_name(a))[0][3]

                        stats.append(StatObject(1510, 0, f"Maycasts {card_name} ({object_name.decode()})"))

                    # Speed bonus
                    case 5:
                        stats.append(StatObject(1350, a, f"% {emojis.SPEED}"))

                    # Passengers
                    case 6:
                        stats.append(StatObject(1340, a, f" Passenger Mount"))

        stats = sorted(stats, key=lambda stat: stat.order)
        _return_stats = []
        for raw_stat in stats:
            raw_stat: StatObject
            _return_stats.append(raw_stat.to_string())

        return _return_stats

    async def build_item_embed(self, row) -> discord.Embed:
        item_id = row[0]
        object_name = row[2].decode()
        set_bonus = row[3]
        rarity = database.translate_rarity(row[4])
        jewels = row[5]
        kind = database.ItemKind(row[6])
        extra_flags = database.ExtraFlags(row[7])
        school = row[8]
        equip_level = row[9]
        min_pet_level = row[10]
        max_spells = row[11]
        max_copies = row[12]
        max_school_copies = row[13]
        deck_school = row[14]
        max_tcs = row[15]
        item_name = row[18]

        requirements = []
        if equip_level != 0:
            requirements.append(f"Level {equip_level}+")
        requirements.append(database.translate_equip_school(school))

        stats = []
        if database.ExtraFlags.PET_JEWEL in extra_flags:
            stats.append(f"Level {database.translate_pet_level(min_pet_level)}+")
        elif kind == database.ItemKind.DECK:
            stats.append(f"Max spells {max_spells}")
            stats.append(f"Max copies {max_copies}")
            stats.append(
                f"Max {database.translate_school(deck_school)} copies {max_school_copies}"
            )
            stats.append(f"Sideboard {max_tcs}")
        stats.extend(await self.fetch_item_stats(item_id))

        embed = (
            discord.Embed(
                color=database.make_school_color(school),
                description="\n".join(stats) or "\u200b",
            )
            .set_author(name=f"{item_name}\n({object_name}: {item_id})", icon_url=database.get_item_icon_url(kind))
            .add_field(name="Requirements", value="\n".join(requirements))
        )

        if jewels != 0:
            embed = embed.add_field(
                name="Sockets", value=database.format_sockets(jewels)
            )

        if set_bonus != 0:
            set_name = await self.fetch_set_bonus_name(set_bonus)
            embed = embed.add_field(name="Set Bonus", value=set_name)

        emoji_flags = database.translate_flags(extra_flags)
        if len(emoji_flags) > 0:
            embed.add_field(name="Flags", value="".join(emoji_flags))

        return embed

    @app_commands.command(name="find", description="Finds a Wizard101 item by name")
    @app_commands.describe(name="The name of the item to search for")
    async def find(
        self, 
        interaction: discord.Interaction, 
        name: str,
        school: Optional[Literal["Any", "Fire", "Ice", "Storm", "Myth", "Life", "Death", "Balance"]] = "Any",
        kind: Optional[Literal["Any", "Hat", "Robe", "Shoes", "Weapon", "Athame", "Amulet", "Ring", "Deck", "Jewel", "Mount"]] = "Any",
        level: Optional[int] = -1,
        use_object_name: Optional[bool] = False
    ):
        await interaction.response.defer()
        if type(interaction.channel) is PartialMessageable:
            logger.info("{} requested item '{}'", interaction.user.name, name)
        else:
            logger.info("{} requested item '{}' in channel #{} of {}", interaction.user.name, name, interaction.channel.name, interaction.guild.name)

        if use_object_name:
            rows = await self.fetch_object_name(name)
            if not rows:
                embed = discord.Embed(description=f"No items with object name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                await interaction.followup.send(embed=embed)
        else:
            rows = await self.fetch_items_with_filter(items=name, school=school, kind=kind, level=level, return_row=True)
            if not rows:
                filtered_rows = await self.fetch_items_with_filter(items=self.bot.item_list, school=school, kind=kind, level=level, return_row=True)
                closest_rows = [(row, fuzz.token_set_ratio(name, row[-1]) + fuzz.ratio(name, row[-1])) for row in filtered_rows]
                closest_rows = sorted(closest_rows, key=lambda x: x[1], reverse=True)
                closest_rows = list(zip(*closest_rows))[0]
                
                rows = await self.fetch_items_with_filter(items=closest_rows[0][-1], school=school, kind=kind, level=level, return_row=True)
                if rows:
                    logger.info("Failed to find '{}' instead searching for {}", name, closest_rows[0][-1])
        
        if rows:
            view = ItemView([await self.build_item_embed(row) for row in rows])
            await view.start(interaction)
        elif not use_object_name:
            embed = discord.Embed(description=f"No items with name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="list", description="Finds a list of item names that contain the string")
    @app_commands.describe(name="The name of the items to search for")
    async def list_names(
        self, 
        interaction: discord.Interaction, 
        name: str,
        school: Optional[Literal["Any", "Fire", "Ice", "Storm", "Myth", "Life", "Death", "Balance"]] = "Any",
        kind: Optional[Literal["Any", "Hat", "Robe", "Shoes", "Weapon", "Athame", "Amulet", "Ring", "Deck", "Jewel", "Mount"]] = "Any",
        level: Optional[int] = -1,
    ):
        await interaction.response.defer()
        if type(interaction.channel) is PartialMessageable:
            logger.info("{} searched for items that contain '{}'", interaction.user.name, name)
        else:
            logger.info("{} searched for items that contain '{}' in channel #{} of {}", interaction.user.name, name, interaction.channel.name, interaction.guild.name)

        items_containing_name = []
        for item in self.bot.item_list:
            item: str

            if name == '*' or name.lower() in item.lower():
                items_containing_name.append(item)

        if len(items_containing_name) > 0:
            no_duplicate_items = [*set(items_containing_name)]
            filtered_items = await self.fetch_items_with_filter(items=no_duplicate_items, school=school, kind=kind, level=level)
            no_no_duplicate_items = [*set(filtered_items)]
            alphabetic_items = sorted(no_no_duplicate_items)

            chunks = [alphabetic_items[i:i+15] for i in range(0, len(alphabetic_items), 15)]
            item_embeds = []
            for item_chunk in chunks:
                embed = (
                    discord.Embed(
                        description="\n".join(item_chunk) or "\u200b",
                    )
                    .set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                )
                item_embeds.append(embed)

            view = ItemView(item_embeds)
            await view.start(interaction)

        else:
            txt = f"Unable to find {name}."

            embed = discord.Embed(description=txt).set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)

            await interaction.followup.send(embed=embed)

        
        



async def setup(bot: TheBot):
    await bot.add_cog(Stats(bot))
