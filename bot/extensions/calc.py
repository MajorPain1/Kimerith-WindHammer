import discord
from discord import app_commands, PartialMessageable, DMChannel
from discord.ext import commands
from loguru import logger
from typing import List, Optional, Literal

from .. import TheBot, database

class Calc(commands.Cog):
    def __init__(self, bot: TheBot):
        self.bot = bot

    @app_commands.command(name="calc", description="Simple Calculation of Damage")
    @app_commands.describe(buffs="Your buffs separated by a space (use a \"P\" prefix to denote pierce) EX: 35 35 40 20P -50P")
    async def find(
        self, 
        interaction: discord.Interaction,
        base: int,
        damage: int,
        pierce: int,
        critical: int,
        resist: int,
        block: int,
        buffs: Optional[str] = "",
        pvp: Optional[bool] = True,
    ):
        await interaction.response.defer()
        
        if type(interaction.channel) is DMChannel or type(interaction.channel) is PartialMessageable:
            logger.info("{} requested calc", interaction.user.name)
        else:
            logger.info("{} requested calc in channel #{} of {}", interaction.user.name, interaction.channel.name, interaction.guild.name)
        
        buffs_as_modifiers = database.translate_buffs(buffs)
        buffs_as_modifiers.append(database.Buff(float(-resist), True))
        no_crit, crit = database.calc_damage(base, damage, pierce, critical, buffs_as_modifiers, block, pvp)
        embed = (
            discord.Embed(
                title=f"Damage Calculator",
                color=discord.Color.dark_blue(),
                description=f"{base}{database.DAMAGE} Base\n\nStats:\n{damage}% {database.DAMAGE}\n{pierce}% {database.PIERCE}\n{critical} {database.CRIT}\n{resist}% {database.RESIST}\n{block} {database.BLOCK}\n\nBuffs: {buffs}"
            )
            .add_field(name="No Crit Damage", value=f"{no_crit:,}{database.DAMAGE}")
            .add_field(name="Crit Damage", value=f"{crit:,}{database.DAMAGE}")
        )

        await interaction.followup.send(embed=embed)

        



async def setup(bot: TheBot):
    await bot.add_cog(Calc(bot))
