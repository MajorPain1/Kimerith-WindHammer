from typing import List, Optional, Literal
from fuzzywuzzy import process, fuzz
from operator import itemgetter

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from .. import TheBot

HELP_DESCRIPTION = """
**/help**: Displays this message\n
**/item find**: Finds the item's ingame stats. Parameters: Name, School, Kind, Level\n
**/item list**: Finds a list of items containing a given string. Parameters: Name, School, Kind, Level\n
**/mob find**: Finds the mob's ingame stats. Parameters: Name, School, Kind, Rank\n
**/mob list**: Finds a list of mobs containing a given string. Parameters: Name, School, Kind, Rank\n
**/mob deck**: Finds a mob's deck. Parameters: Name, School, Kind, Rank\n
**/mob calc**: Calculate damage against a mob. Parameters: Name, School, Base, Damage, Pierce, Critical, Buffs\n
**/spell find**: Finds the spell as shown in the files. Parameters: Name, School, Kind, Rank\n
**/spell list**: Finds a list of spells containing a given string. Parameters: Name, School, Kind, Rank\n
**/pet find**: Finds the pet as shown in the files. Parameters: Name, School, Wow, Exclusive\n
**/pet list**: Finds a list of pets containing a given string. Parameters: Name, School, Wow, Exclusive\n
**/fish find**: Finds the fish as shown in the files. Parameters: Name, School, Wow, Exclusive\n
**/fish list**: Finds a list of fish containing a given string. Parameters: Name, School, Rank, Is_Sentinel\n
**/statcaps find**: Gives the stat caps for a given school and level. Parameters: Level, School\n
**/calc**: Calculate damage in Wizard101. Parameters: Base, Damage, Pierce, Critical, Resist, Buffs\n
"""

class Help(commands.Cog):
    def __init__(self, bot: TheBot):
        self.bot = bot

    @app_commands.command(name="help", description="Provides a list of commands Kimerith WindHammer can do")
    async def find(
        self, 
        interaction: discord.Interaction, 
    ):
        embed = discord.Embed(
            title=f"Kimerith WindHammer's commands",
            color=discord.Color.dark_blue(),
            description=HELP_DESCRIPTION,
        )

        await interaction.response.send_message(embed=embed)

        



async def setup(bot: TheBot):
    await bot.add_cog(Help(bot))
