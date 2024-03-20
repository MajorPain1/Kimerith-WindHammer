from typing import List, Optional, Literal
from fuzzywuzzy import process, fuzz
from operator import itemgetter

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from ..database import StatObject
from .. import TheBot, database, emojis
from ..menus import ItemView


FIND_MOB_QUERY = """
SELECT * FROM mobs
INNER JOIN locale_en ON locale_en.id == mobs.name
WHERE locale_en.data == ? COLLATE NOCASE
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
        filtered_mobs = []

        if type(mobs) == str:
            list_mob = []
            list_mob.append(mobs)
            mobs = list_mob

        for mob in mobs:
            rows = await self.fetch_mob(mob)
            for row in rows:
                school_idx = row[7] - 2
                title = row[4]
                mob_rank = row[5]

                matches_school = school == "Any" or school_idx == database._SCHOOLS_STR.index(school)
                matches_kind =  kind == "Any" or title == kind
                matches_level = rank == -1 or mob_rank == rank

                if matches_school and matches_kind and matches_level:
                    if return_row:
                        filtered_mobs.append(row)
                    else:
                        filtered_mobs.append(row[-1])

        return filtered_mobs

    async def fetch_mob_stats(self, mob: int) -> List[str]:
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
                            stats.append(StatObject(132, a, f"{emojis.PIP}"))
                        if b != 0:
                            stats.append(StatObject(133, b, f"{emojis.POWER_PIP}"))

                    # Speed bonus
                    case 5:
                        stats.append(StatObject(134, a, f"{emojis.SPEED}"))

        stats = sorted(stats, key=lambda stat: stat.order)

        return stats
    
    async def fetch_mob_items(self, mob: int) -> List[str]:
        items = []

        async with self.bot.db.execute(
            "SELECT * FROM mob_items WHERE mob == ?", (mob,)
        ) as cursor:
            async for row in cursor:
                items.append(row[2])

        return items


    async def build_mob_embed(self, row) -> discord.Embed:
        mob_id = row[0]
        real_name = row[2].decode("utf-8") 
        image_file = row[3].decode("utf-8")
        title = row[4]
        rank = row[5]
        hp = row[6]
        school = row[7]
        secondary_school = row[8]
        max_shadow = row[9]
        has_cheats = row[10]
        intelligence = row[11]
        selfishness = row[12]
        aggressiveness = row[13]
        monstro = database.MonstrologyKind(row[14])
        mob_name = row[16]

        ai = [f"Intelligence {intelligence}", f"Selfishness {selfishness}", f"Aggressiveness {aggressiveness}"]

        stats = await self.fetch_mob_stats(mob_id)
        items = await self.fetch_mob_items(mob_id)
        await database.sum_stats(self.bot.db, stats, items)

        stats = sorted(stats, key=lambda stat: stat.order)
        _return_stats = []
        for stat in stats:
            _return_stats.append(stat.to_string())

        stats = _return_stats

        flags = []
        if secondary_school:
            flags.append(f"Secondary School {database.translate_school(secondary_school)}")
        if bool(has_cheats):
            flags.append(f"This {title} Mob Cheats!")
        if max_shadow > 0:
            stats.append(f"Max {max_shadow} {emojis.SHADOW_PIP}")
        
        extracts = database.get_monstrology_string(monstro)

        embed = (
            discord.Embed(
                color=database.make_school_color(school),
                description="\n".join(stats) or "\u200b",
            )
            .set_author(name=f"{mob_name} ({real_name})\nHP {hp}\nRank {rank} {title}", icon_url=database.translate_school(school).url)
            .add_field(name="AI", value="\n".join(ai))
        )

        if flags:
            embed.add_field(name="Flags", value="\n".join(flags))

        if extracts:
            embed.add_field(name="Extracts", value="\n".join(extracts))

        discord_file = None
        if image_file:
            try:
                image_name = image_file.split(".")[0]
                png_file = f"{image_name}.png"
                png_name = png_file.replace(" ", "")
                discord_file = discord.File(f"PNG_Images\\{png_name}", filename=png_name)
                embed.set_thumbnail(url=f"attachment://{png_name}")
            except FileNotFoundError:
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
        logger.info("Requested mob '{}'", name)

        if use_object_name:
            rows = await self.fetch_object_name(name)
            if not rows:
                embed = discord.Embed(description=f"No mobs with object name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                await interaction.followup.send(embed=embed)
        else:
            rows = await self.fetch_mobs_with_filter(name, school, kind, rank, return_row=True)
            if not rows:
                closest_names = [(string, fuzz.token_set_ratio(name, string) + fuzz.ratio(name, string)) for string in self.bot.mob_list]
                closest_names = sorted(closest_names, key=lambda x: x[1], reverse=True)
                closest_names = list(zip(*closest_names))[0]

                for mob in closest_names:
                    rows = await self.fetch_mobs_with_filter(mob, school, kind, rank, return_row=True)

                    if rows:
                        logger.info("Failed to find '{}' instead searching for {}", name, mob)
                        break
                    else:
                        logger.info("Failed to find '{}'", name)
                        break

        if rows:
            embeds = [await self.build_mob_embed(row) for row in rows]
            sorted_embeds = sorted(embeds, key=lambda embed: embed[0].author.name)
            unzipped_embeds, unzipped_images = list(zip(*sorted_embeds))
            view = ItemView(unzipped_embeds, files=unzipped_images)
            await view.start(interaction)

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
        logger.info("Search for mobs that contain '{}'", name)

        mobs_containing_name = []
        for mob in self.bot.mob_list:
            mob: str

            if name.lower() in mob.lower():
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

        
        



async def setup(bot: TheBot):
    await bot.add_cog(Mobs(bot))
