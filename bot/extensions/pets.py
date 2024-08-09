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

FIND_PET_QUERY = """
SELECT * FROM pets
LEFT JOIN locale_en ON locale_en.id == pets.name
WHERE locale_en.data == ? COLLATE NOCASE
"""

FIND_OBJECT_NAME_QUERY = """
SELECT * FROM pets
INNER JOIN locale_en ON locale_en.id == pets.name
WHERE pets.real_name == ? COLLATE NOCASE
"""

SPELL_NAME_ID_QUERY = """
SELECT locale_en.data FROM spells
INNER JOIN locale_en ON locale_en.id == spells.name
WHERE spells.real_name == ?
"""

EGG_NAME_ID_QUERY = """
SELECT locale_en.data FROM spells
INNER JOIN locale_en ON locale_en.id == spells.name
WHERE spells.real_name == ?
"""

SET_BONUS_NAME_QUERY = """
SELECT locale_en.data FROM set_bonuses
INNER JOIN locale_en ON locale_en.id == set_bonuses.name
WHERE set_bonuses.id == ?
"""

FIND_ITEMCARD_OBJECT_NAME_QUERY = """
SELECT * FROM spells
WHERE spells.template_id == ? COLLATE NOCASE
"""

TALENT_NAME_ID_QUERY = """
SELECT * FROM talents
INNER JOIN locale_en ON locale_en.id == talents.talent
WHERE talents.pet == ?
"""

EGG_NAME_ID_QUERY = """
SELECT data FROM locale_en
WHERE locale_en.id == ?
"""

def remove_indices(lst, indices):
    return [value for index, value in enumerate(lst) if index not in indices]

class Pets(commands.GroupCog, name="pet"):
    def __init__(self, bot: TheBot):
        self.bot = bot

    async def fetch_pet(self, name: str) -> List[tuple]:
        async with self.bot.db.execute(FIND_PET_QUERY, (name,)) as cursor:
            return await cursor.fetchall()
        
    async def fetch_egg_name(self, name: str) -> List[tuple]:
        async with self.bot.db.execute(EGG_NAME_ID_QUERY, (name,)) as cursor:
            return await cursor.fetchall()
        
    async def fetch_object_name(self, name: str) -> List[tuple]:
        name_bytes = name.encode('utf-8')
        async with self.bot.db.execute(FIND_OBJECT_NAME_QUERY, (name_bytes,)) as cursor:
            return await cursor.fetchall()
        
    async def fetch_itemcard_object_name(self, id: str) -> List[tuple]:
        async with self.bot.db.execute(FIND_ITEMCARD_OBJECT_NAME_QUERY, (id,)) as cursor:
            return await cursor.fetchall()
        
    async def fetch_pets_with_filter(self, pets: List[str], school: Optional[str] = "Any", wow: Optional[int] = -1, exclusive: Optional[bool] = None, return_row=False):
        filtered_pets = []

        if type(pets) == str:
            list_pet = []
            list_pet.append(pets)
            pets = list_pet

        for pet in pets:
            rows = await self.fetch_pet(pet)
            for row in rows:
                school_idx = row[8] - 2
                wow_idx = row[6]
                exclusive_idx = bool(row[7])

                matches_school = school == "Any" or school_idx == database._SCHOOLS_STR.index(school)
                matches_kind =  wow == -1 or wow_idx == wow
                matches_rank = exclusive == None or exclusive == exclusive_idx

                if matches_school and matches_kind and matches_rank:
                    if return_row:
                        filtered_pets.append(row)
                    else:
                        filtered_pets.append(row[-1])
                    
        return filtered_pets

    
    async def fetch_pet_talents(self, id: str) -> List[tuple]:
        async with self.bot.db.execute(TALENT_NAME_ID_QUERY, (id,)) as cursor:
            return await cursor.fetchall()
    
    async def fetch_pet_cards(self, pet: int) -> List[str]:
        card_onames = []
        async with self.bot.db.execute(
            "SELECT * FROM pet_cards WHERE pet == ?", (pet,)
        ) as cursor:
            async for row in cursor:
                card_onames.append(row[-1])

        card_names = []
        for card in card_onames:
            async with self.bot.db.execute(SPELL_NAME_ID_QUERY, (card,)) as cursor:
                card_name = await cursor.fetchone()

            object_name = card.decode()

            card_names.append(f"{card_name[0]} ({object_name})")

        return card_names
    
    async def fetch_set_bonus_name(self, set_id: int) -> Optional[tuple]:
        async with self.bot.db.execute(SET_BONUS_NAME_QUERY, (set_id,)) as cursor:
            return (await cursor.fetchone())[0]
    
    
    def format_card_string(self, cards) -> str:
        res = ""
        for card in cards:
            res += card + "\n"

        return res

    async def build_pet_embed(self, row):
        pet_id = row[0]
        real_name = row[2].decode("utf-8")
        set_bonus = row[3]
        rarity = row[4]
        extra_flags = database.ExtraFlags(row[5])
        wow_factor = row[6]
        exclusive = row[7]
        school = row[8]
        egg = await self.fetch_egg_name(row[9])
        
        strength = row[10]
        intellect = row[11]
        agility = row[12]
        will = row[13]
        power = row[14]

        pet_name = row[-1]

        talents = await self.fetch_pet_talents(pet_id)
        cards = await self.fetch_pet_cards(pet_id)

        talents_unsorted = []
        for talent in talents[:10]:
            talents_unsorted.append(talent)
        talents_sorted = sorted(talents_unsorted, key=lambda talent: talent[1])
        talent_string = ""
        for talent in talents_sorted:
            talent_string += talent[-1] + "\n"

        derby_unsorted = []
        for talent in talents[10:]:
            derby_unsorted.append(talent)
        derby_sorted = sorted(derby_unsorted, key=lambda talent: talent[1])
        derby_string = ""
        for talent in derby_sorted:
            derby_string += talent[-1] + "\n"

        embed = (
            discord.Embed(
                title=f"Wow {wow_factor}" + " Exclusive" * exclusive,
                color=database.make_school_color(school),
            )
            .set_author(name=f"{pet_name}\n({real_name}: {pet_id})\n{egg[0][0]}", icon_url=database.translate_school(school).url)
            .add_field(name="Talents", value=talent_string, inline=True)
            .add_field(name="Derby", value=derby_string, inline=True)
            .add_field(name="Stats", value=f"{strength} Strength\n{intellect} Intellect\n{agility} Agility\n{will} Will\n{power} Power\n", inline=False)
        )

        if len(cards) > 0:
            cards_string = self.format_card_string(cards)
            embed = embed.add_field(name="Cards", value=cards_string)


        if set_bonus != 0:
            set_name = await self.fetch_set_bonus_name(set_bonus)
            embed = embed.add_field(name="Set Bonus", value=set_name)


        emoji_flags = database.translate_flags(extra_flags)
        if len(emoji_flags) > 0:
            embed.add_field(name="Flags", value="".join(emoji_flags))

        return embed


    @app_commands.command(name="find", description="Finds a Wizard101 pet by name")
    @app_commands.describe(name="The name of the pet to search for")
    async def find(
        self, 
        interaction: discord.Interaction, 
        name: str,
        school: Optional[Literal["Any", "Fire", "Ice", "Storm", "Myth", "Life", "Death", "Balance"]] = "Any",
        wow: Optional[int] = -1,
        exclusive: Optional[bool] = None,
        use_object_name: Optional[bool] = False
    ):
        await interaction.response.defer()
        if type(interaction.channel) is PartialMessageable:
            logger.info("{} requested pet '{}'", interaction.user.name, name)
        else:
            logger.info("{} requested pet '{}' in channel #{} of {}", interaction.user.name, name, interaction.channel.name, interaction.guild.name)

        if use_object_name:
            rows = await self.fetch_object_name(name)
            if not rows:
                embed = discord.Embed(description=f"No pets with object name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                await interaction.followup.send(embed=embed)
                
        else:
            rows = await self.fetch_pets_with_filter(name, school, wow, exclusive, return_row=True)
            if not rows:
                closest_names = [(string, fuzz.token_set_ratio(name, string) + fuzz.ratio(name, string)) for string in self.bot.pet_list]
                closest_names = sorted(closest_names, key=lambda x: x[1], reverse=True)
                closest_names = list(zip(*closest_names))[0]
                
                for pet in closest_names:
                    rows = await self.fetch_pets_with_filter(pet, school, wow, exclusive, return_row=True)

                    if rows:
                        logger.info("Failed to find '{}' instead searching for {}", name, pet)
                        break

        if rows:
            view = ItemView([await self.build_pet_embed(row) for row in rows])
            await view.start(interaction)

    @app_commands.command(name="list", description="Finds a list of pet names that contain the string")
    @app_commands.describe(name="The name of the pets to search for")
    async def list_names(
        self, 
        interaction: discord.Interaction, 
        name: str,
        school: Optional[Literal["Any", "Fire", "Ice", "Storm", "Myth", "Life", "Death", "Balance"]] = "Any",
        wow: Optional[int] = -1,
        exclusive: Optional[bool] = None,
    ):
        await interaction.response.defer()
        if type(interaction.channel) is PartialMessageable:
            logger.info("{} searched for pets that contain '{}'", interaction.user.name, name)
        else:
            logger.info("{} searched for pets that contain '{}' in channel #{} of {}", interaction.user.name, name, interaction.channel.name, interaction.guild.name)

        pets_containing_name = []
        for pet in self.bot.pet_list:
            pet: str

            if name.lower() in pet.lower():
                pets_containing_name.append(pet)

        no_duplicate_pets = [*set(pets_containing_name)]
        filtered_pets = await self.fetch_pets_with_filter(pets=no_duplicate_pets, school=school, wow=wow, exclusive=exclusive)
        no_no_duplicate_pets = [*set(filtered_pets)]
        alphabetic_pets = sorted(no_no_duplicate_pets)

        if len(alphabetic_pets) > 0:
            chunks = [alphabetic_pets[i:i+15] for i in range(0, len(alphabetic_pets), 15)]
            pet_embeds = []
            for pet_chunk in chunks:
                embed = (
                    discord.Embed(
                        description="\n".join(pet_chunk) or "\u200b",
                    )
                    .set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                )
                pet_embeds.append(embed)

            view = ItemView(pet_embeds)
            await view.start(interaction)

        else:
            embed = discord.Embed(description=f"Unable to find {name}.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)

            await interaction.followup.send(embed=embed)

        
        



async def setup(bot: TheBot):
    await bot.add_cog(Pets(bot))
