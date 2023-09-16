from typing import List, Optional, Literal
from fuzzywuzzy import process, fuzz
from operator import attrgetter
import re

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from .. import TheBot, database, emojis
from ..menus import ItemView

FIND_SPELL_QUERY = """
SELECT * FROM spells
LEFT JOIN locale_en ON locale_en.id == spells.name
WHERE locale_en.data == ? COLLATE NOCASE
"""

FIND_OBJECT_NAME_QUERY = """
SELECT * FROM spells
INNER JOIN locale_en ON locale_en.id == spells.name
WHERE spells.real_name == ? COLLATE NOCASE
"""

SPELL_DESCRIPTION_QUERY = """
SELECT locale_en.data FROM spells
JOIN locale_en ON spells.description = locale_en.id
WHERE spells.description = ? COLLATE NOCASE
"""

def remove_indices(lst, indices):
    return [value for index, value in enumerate(lst) if index not in indices]

class Spells(commands.GroupCog, name="spell"):
    def __init__(self, bot: TheBot):
        self.bot = bot

    async def fetch_spell(self, name: str) -> List[tuple]:
        async with self.bot.db.execute(FIND_SPELL_QUERY, (name,)) as cursor:
            return await cursor.fetchall()
        
    async def fetch_object_name(self, name: str) -> List[tuple]:
        name_bytes = name.encode('utf-8')
        async with self.bot.db.execute(FIND_OBJECT_NAME_QUERY, (name_bytes,)) as cursor:
            return await cursor.fetchall()
        
    async def fetch_spells_with_filter(self, spells: List[str], school: Optional[str] = "Any", kind: Optional[str] = "Any", rank: Optional[int] = -1, return_row=False):
        filtered_spells = []

        if type(spells) == str:
            list_spell = []
            list_spell.append(spells)
            spells = list_spell

        for spell in spells:
            rows = await self.fetch_spell(spell)
            for row in rows:
                school_idx = row[7] - 2
                kind_idx = row[9]
                spell_rank = row[10]

                matches_school = school == "Any" or school_idx == database._SCHOOLS_STR.index(school)
                matches_kind =  kind == "Any" or kind_idx == database._SPELL_TYPES_STR.index(kind)
                matches_rank = rank == -1 or spell_rank == rank

                if matches_school and matches_kind and matches_rank:
                    if return_row:
                        filtered_spells.append(row)
                    else:
                        filtered_spells.append(row[-1])
                    
        return filtered_spells
    
    async def fetch_description(self, flag: int) -> List[tuple]:
        async with self.bot.db.execute(SPELL_DESCRIPTION_QUERY, (flag,)) as cursor:
            return await cursor.fetchall()
    
    async def fetch_spell_effects(self, spell: int) -> List[str]:
        res = []
        async with self.bot.db.execute(
            "SELECT * FROM effects WHERE spell == ?", (spell,)
        ) as cursor:
            async for row in cursor:
                res.append(row[2:])

        res = sorted(res, key=lambda effect: effect[0])
        return [(tup[1],) + (database.translate_school(tup[2]),) + (tup[3],) for tup in res]


    def parse_description(self, description, effects: List[tuple]) -> str:
        description = re.sub(r'#-?\d+:', '', description)
        description = re.sub("<[^>]*>", "", description)
        description = re.sub(r"\{[^{}]*\}", "", description)
        for variable in re.findall(r"\$(\w+?)(\d*)\$", description):

            markdown_variable = variable[0]
            index = variable[1]
            actual = variable[0] + variable[1]

            if index:
                index = int(index) - 1
            else:
                index = 0

            match markdown_variable:
                case "eA" | "eAPerPip" | "eAPerPipAll":
                    if actual == "eA1":
                        description = description.replace(f'${actual}$', "")
                    elif index >= len(effects):
                        description = description.replace(f'${actual}$', "")
                    else:
                        description = description.replace(f'${actual}$', f"{effects[index][0]}")

                case "eABonus":
                    description = description.replace(f'${actual}$', "").lstrip()
                
                case "eAExtra":
                    description = description.replace(f'\\n+${actual}$', "")

                case "eARounds":
                    if index >= len(effects):
                        description = description.replace(f'${actual}$', "")
                    else:
                        description = description.replace(f'${actual}$', f"{effects[index][2]}")

                case "dT_image":
                    if index >= len(effects):
                        description = description.replace(f'${actual}$', f"")
                    else:
                        description = description.replace(f'${actual}$', f"{effects[index][1]}")

                case _:
                    description = description.replace(f'${actual}$', f"{database.translate_type_emoji(markdown_variable)}")


        return description.replace("\\n", "\n").replace("\\r", "\r")
        
    async def build_spell_embed(self, row):
        spell_id = row[1]
        real_name = row[3].decode("utf-8")
        image_file = row[4]
        accuracy = row[5]
        energy = row[6]
        school = row[7]
        description = row[8]
        type_name = row[9]

        rank = row[10]
        x_pips = row[11]
        shadow_pips = row[12] * f"{emojis.SHADOW_PIP}"
        fire_pips = row[13] * f"{emojis.FIRE}"
        ice_pips = row[14] * f"{emojis.ICE}"
        storm_pips = row[15] * f"{emojis.STORM}"
        myth_pips = row[16] * f"{emojis.MYTH}"
        life_pips = row[17] * f"{emojis.LIFE}"
        death_pips = row[18] * f"{emojis.DEATH}"
        balance_pips = row[19] * f"{emojis.BALANCE}"

        if x_pips:
            rank = "X"

        add_plus_sign = "+ " * any([shadow_pips, fire_pips, ice_pips, storm_pips, myth_pips, life_pips, death_pips, balance_pips])
        pip_count = f"Rank {rank} {add_plus_sign}{shadow_pips}{fire_pips}{ice_pips}{storm_pips}{myth_pips}{life_pips}{death_pips}{balance_pips}"

        effects = await self.fetch_spell_effects(spell_id)

        if not effects:
            effects.append((0, 0, 0))

        spell_name = row[-1]

        raw_description = await self.fetch_description(description)
        if raw_description:
            while type(raw_description) != str:
                raw_description = raw_description[0]

            parsed_description = self.parse_description(raw_description, effects)
        else:
            parsed_description = "Description Not Found"

        if school == 12:
            type_string = database.GARDENING_TYPES[type_name]
        elif school == 14:
            type_string = database.FISHING_TYPES[type_name]
        elif school == 15:
            type_string = database.CANTRIP_TYPES[type_name]
        else:
            type_string = database._SPELL_TYPES[type_name]

        if school in (12, 14, 15):
            accuracy_field = f"Costs {energy} {emojis.ENERGY}"
        else:
            accuracy_field = f"{accuracy}% {emojis.ACCURACY}"
        
        embed = (
            discord.Embed(
                title=pip_count,
                color=database.make_school_color(school),
                description=parsed_description or "\u200b",
            )
            .set_author(name=f"{spell_name}\n({real_name})", icon_url=database.translate_school(school).url)
            .add_field(name=accuracy_field, value="")
            .add_field(name=f"Type {type_string}", value="")
        )

        discord_file = None
        if image_file:
            try:
                image_name = image_file.split(".")[0]
                png_file = f"{image_name}.png"
                png_name = png_file.replace(" ", "")
                discord_file = discord.File(f"PNG_Images\\{png_file}", filename=png_name)
                embed.set_thumbnail(url=f"attachment://{png_name}")
            except FileNotFoundError:
                pass

        return embed, discord_file


    @app_commands.command(name="find", description="Finds a Wizard101 spell by name")
    @app_commands.describe(name="The name of the spell to search for")
    async def find(
        self, 
        interaction: discord.Interaction, 
        name: str,
        school: Optional[Literal["Any", "Fire", "Ice", "Storm", "Myth", "Life", "Death", "Balance", "Star", "Sun", "Moon", "Gardening", "Shadow", "Fishing", "Cantrips", "Castlemagic", "WhirlyBurly"]] = "Any",
        kind: Optional[Literal["Any","Healing","Damage","Charm","Ward","Aura","Global","AOE","Steal","Manipulation","Enchantment","Polymorph","Curse","Jinx","Mutate","Cloak"]] = "Any",
        rank: Optional[int] = -1,
        use_object_name: Optional[bool] = False
    ):
        await interaction.response.defer()
        logger.info("Requested spell '{}'", name)

        if use_object_name:
            rows = await self.fetch_object_name(name)
            if not rows:
                embed = discord.Embed(description=f"No spells with object name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                await interaction.followup.send(embed=embed)
                
        else:
            rows = await self.fetch_spells_with_filter(name, school, kind, rank, return_row=True)
            if not rows:
                closest_names = [(string, fuzz.token_set_ratio(name, string) + fuzz.ratio(name, string)) for string in self.bot.spell_list]
                closest_names = sorted(closest_names, key=lambda x: x[1], reverse=True)
                closest_names = list(zip(*closest_names))[0]
                
                for spell in closest_names:
                    rows = await self.fetch_spells_with_filter(spell, school, kind, rank, return_row=True)

                    if rows:
                        logger.info("Failed to find '{}' instead searching for {}", name, spell)
                        break
        if rows:
            embeds = [await self.build_spell_embed(row) for row in rows]
            sorted_embeds = sorted(embeds, key=lambda embed: embed[0].author.name)
            unzipped_embeds, unzipped_images = list(zip(*sorted_embeds))
            view = ItemView(unzipped_embeds, files=unzipped_images)
            await view.start(interaction)

    @app_commands.command(name="list", description="Finds a list of spell names that contain the string")
    @app_commands.describe(name="The name of the spells to search for")
    async def list_names(
        self, 
        interaction: discord.Interaction, 
        name: str,
        school: Optional[Literal["Any", "Fire", "Ice", "Storm", "Myth", "Life", "Death", "Balance", "Star", "Sun", "Moon", "Gardening", "Shadow", "Fishing", "Cantrips", "Castlemagic", "WhirlyBurly"]] = "Any",
        kind: Optional[Literal["Any","Healing","Damage","Charm","Ward","Aura","Global","AOE","Steal","Manipulation","Enchantment","Polymorph","Curse","Jinx","Mutate","Cloak"]] = "Any",
        rank: Optional[int] = -1,
    ):
        await interaction.response.defer()
        logger.info("Search for spells that contain '{}'", name)

        spells_containing_name = []
        for spell in self.bot.spell_list:
            spell: str

            if name.lower() in spell.lower():
                spells_containing_name.append(spell)

        no_duplicate_spells = [*set(spells_containing_name)]
        filtered_spells = await self.fetch_spells_with_filter(spells=no_duplicate_spells, school=school, kind=kind, rank=rank)
        no_no_duplicate_spells = [*set(filtered_spells)]
        alphabetic_spells = sorted(no_no_duplicate_spells)

        if len(alphabetic_spells) > 0:
            chunks = [alphabetic_spells[i:i+15] for i in range(0, len(alphabetic_spells), 15)]
            spell_embeds = []
            for spell_chunk in chunks:
                embed = (
                    discord.Embed(
                        description="\n".join(spell_chunk) or "\u200b",
                    )
                    .set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                )
                spell_embeds.append(embed)

            view = ItemView(spell_embeds)
            await view.start(interaction)

        else:
            embed = discord.Embed(description=f"No spells containing {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)

            await interaction.followup.send(embed=embed)

        
        



async def setup(bot: TheBot):
    await bot.add_cog(Spells(bot))
