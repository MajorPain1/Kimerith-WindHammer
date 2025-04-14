from typing import List, Optional, Literal
from fuzzywuzzy import process, fuzz
from operator import attrgetter
import re
from random import choice

import discord
from discord import app_commands, PartialMessageable
from discord.ext import commands
from loguru import logger

from .. import TheBot, database, emojis
from ..menus import ItemView

FIND_FISH_QUERY = """
SELECT * FROM fish
LEFT JOIN locale_en ON locale_en.id == fish.name
WHERE locale_en.data == ? COLLATE NOCASE
"""

FIND_FISH_WITH_FILTER_QUERY = """
SELECT * FROM fish
INNER JOIN locale_en ON locale_en.id == fish.name
WHERE locale_en.data COLLATE NOCASE IN ({placeholders})
AND (? = 'Any' OR fish.school = ?)
AND (? = -1 OR fish.rank = ?)
AND (? IS NULL OR fish.is_sentinel = ?)
COLLATE NOCASE
"""

FIND_OBJECT_NAME_QUERY = """
SELECT * FROM fish
INNER JOIN locale_en ON locale_en.id == fish.name
WHERE fish.real_name == ? COLLATE NOCASE
"""

def remove_indices(lst, indices):
    return [value for index, value in enumerate(lst) if index not in indices]

class Fish(commands.GroupCog, name="fish"):
    def __init__(self, bot: TheBot):
        self.bot = bot

    async def fetch_fish(self, name: str) -> List[tuple]:
        async with self.bot.db.execute(FIND_FISH_QUERY, (name,)) as cursor:
            return await cursor.fetchall()
        
    async def fetch_object_name(self, name: str) -> List[tuple]:
        name_bytes = name.encode('utf-8')
        async with self.bot.db.execute(FIND_OBJECT_NAME_QUERY, (name_bytes,)) as cursor:
            return await cursor.fetchall()
        
    async def fetch_fish_with_filter(self, fish: List[str], school: Optional[str] = "Any", rank: Optional[int] = -1, is_sentinel: Optional[bool] = None, return_row=False):
        if isinstance(fish, str):
            fish = [fish]

        results = []
        
        school_val = (database._SCHOOLS_STR.index(school) + 2) if school != "Any" else None

        for chunk in database.sql_chunked(fish, 900):  # Stay under SQLite's limit
            placeholders = database._make_placeholders(len(chunk))
            query = FIND_FISH_WITH_FILTER_QUERY.format(placeholders=placeholders)

            args = (
                *chunk,
                school, school_val,
                rank, rank,
                is_sentinel, is_sentinel
            )

            async with self.bot.db.execute(query, args) as cursor:
                rows = await cursor.fetchall()

            if return_row:
                results.extend(rows)
            else:
                results.extend(row[-1] for row in rows)

        return results

    async def build_fish_embed(self, row):
        fish_id = row[0]
        real_name = row[2].decode("utf-8")
        rank = row[3]
        school = row[4]
        base_length = row[5]
        min_size = row[6]
        max_size = row[7]
        speed = row[8]
        bite_seconds = row[9]
        initial_bite_chance = row[10]
        incremental_bite_chance = row[11]
        is_sentinel = row[12]

        fish_name = row[-1]

        embed = (
            discord.Embed(
                title=f"Rank {rank}" + " Sentinel" * is_sentinel,
                color=database.make_school_color(school),
            )
            .set_author(name=f"{fish_name}\n({real_name}: {fish_id})", icon_url=database.translate_school(school).url)
            .add_field(name="Size", value=f"Base: {base_length}\nMinimum: {round(min_size * base_length, 2)} ({min_size})\nMaximum: {round(max_size * base_length, 2)} ({max_size})")
            .add_field(name="Speed", value=f"{speed}")
            .add_field(name="Bite", value=f"Bite Time: {bite_seconds}\nInitial Chance: {initial_bite_chance}\nIncremental Chance: {incremental_bite_chance}")
        )

        return embed


    @app_commands.command(name="find", description="Finds a Wizard101 fish by name")
    @app_commands.describe(name="The name of the fish to search for")
    async def find(
        self, 
        interaction: discord.Interaction, 
        name: str,
        school: Optional[Literal["Any", "Fire", "Ice", "Storm", "Myth", "Life", "Death", "Balance"]] = "Any",
        rank: Optional[int] = -1,
        is_sentinel: Optional[bool] = None,
        use_object_name: Optional[bool] = False
    ):
        await interaction.response.defer()
        if type(interaction.channel) is PartialMessageable:
            logger.info("{} requested fish '{}'", interaction.user.name, name)
        else:
            logger.info("{} requested fish '{}' in channel #{} of {}", interaction.user.name, name, interaction.channel.name, interaction.guild.name)

        if use_object_name:
            rows = await self.fetch_object_name(name)
            if not rows:
                embed = discord.Embed(description=f"No fish with object name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                await interaction.followup.send(embed=embed)
                
        else:
            rows = await self.fetch_fish_with_filter(name, school, rank, is_sentinel, return_row=True)
            if not rows:
                filtered_rows = await self.fetch_fish_with_filter(self.bot.fish_list, school, rank, is_sentinel, return_row=True)
                closest_rows = [(row, fuzz.token_set_ratio(name, row[-1]) + fuzz.ratio(name, row[-1])) for row in filtered_rows]
                closest_rows = sorted(closest_rows, key=lambda x: x[1], reverse=True)
                closest_rows = list(zip(*closest_rows))[0]
                
                rows = await self.fetch_fish_with_filter(closest_rows[0][-1], school, rank, is_sentinel, return_row=True)
                if rows:
                    logger.info("Failed to find '{}' instead searching for {}", name, closest_rows[0][-1])

        if rows:
            view = ItemView([await self.build_fish_embed(row) for row in rows])
            await view.start(interaction)
        elif not use_object_name:
            logger.info("Failed to find '{}'", name)
            embed = discord.Embed(description=f"No fish with name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="list", description="Finds a list of fish names that contain the string")
    @app_commands.describe(name="The name of the fish to search for")
    async def list_names(
        self, 
        interaction: discord.Interaction, 
        name: str,
        school: Optional[Literal["Any", "Fire", "Ice", "Storm", "Myth", "Life", "Death", "Balance"]] = "Any",
        rank: Optional[int] = -1,
        is_sentinel: Optional[bool] = None,
    ):
        await interaction.response.defer()
        if type(interaction.channel) is PartialMessageable:
            logger.info("{} searched for fish that contain '{}'", interaction.user.name, name)
        else:
            logger.info("{} searched for fish that contain '{}' in channel #{} of {}", interaction.user.name, name, interaction.channel.name, interaction.guild.name)

        fish_containing_name = []
        for fish in self.bot.fish_list:
            fish: str

            if name == '*' or name.lower() in fish.lower():
                fish_containing_name.append(fish)

        no_duplicate_fish = [*set(fish_containing_name)]
        filtered_fish = await self.fetch_fish_with_filter(fish=no_duplicate_fish, school=school, rank=rank, is_sentinel=is_sentinel)
        no_no_duplicate_fish = [*set(filtered_fish)]
        alphabetic_fish = sorted(no_no_duplicate_fish)

        if len(alphabetic_fish) > 0:
            chunks = [alphabetic_fish[i:i+15] for i in range(0, len(alphabetic_fish), 15)]
            fish_embeds = []
            for fish_chunk in chunks:
                embed = (
                    discord.Embed(
                        description="\n".join(fish_chunk) or "\u200b",
                    )
                    .set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                )
                fish_embeds.append(embed)

            view = ItemView(fish_embeds)
            await view.start(interaction)

        else:
            embed = discord.Embed(description=f"Unable to find {name}.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)

            await interaction.followup.send(embed=embed)

        
        



async def setup(bot: TheBot):
    await bot.add_cog(Fish(bot))
