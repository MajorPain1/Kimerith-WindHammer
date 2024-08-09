from typing import List, Optional, Literal
from fuzzywuzzy import process, fuzz
from operator import itemgetter
from random import choice

import discord
from discord import app_commands, PartialMessageable
from discord.ext import commands
from loguru import logger

from ..database import StatObject, _SCHOOLS_STR
from .. import TheBot, database, emojis
from ..menus import ItemView


FIND_STAT_CAPS_QUERY = """
SELECT * FROM statcaps WHERE level = ? AND school = ?;
"""


class StatCaps(commands.GroupCog, name="statcaps"):
    def __init__(self, bot: TheBot):
        self.bot = bot

    async def fetch_stat_cap(self, level: int, school: str) -> List[tuple]:
        async with self.bot.db.execute(FIND_STAT_CAPS_QUERY, (level,school,)) as cursor:
            return await cursor.fetchall()

    async def build_stat_cap_embed(self, row) -> discord.Embed:
        level = row[0]
        school = row[1]
        max_pips = row[2]
        max_power_pips = row[3]
        max_health = row[4]
        max_mana = row[5]
        ppc = row[6]
        shad_rating = row[7]
        archmastery = row[8]
        outgoing = row[9]
        incoming = row[10]

        b_acc = row[11]
        d_acc = row[12]
        f_acc = row[13]
        i_acc = row[14]
        l_acc = row[15]
        m_acc = row[16]
        s_acc = row[17]

        b_ap = row[18]
        d_ap = row[19]
        f_ap = row[20]
        i_ap = row[21]
        l_ap = row[22]
        m_ap = row[23]
        s_ap = row[24]

        b_block = row[25]
        d_block = row[26]
        f_block = row[27]
        i_block = row[28]
        l_block = row[29]
        m_block = row[30]
        s_block = row[31]

        b_crit = row[32]
        d_crit = row[33]
        f_crit = row[34]
        i_crit = row[35]
        l_crit = row[36]
        m_crit = row[37]
        s_crit = row[38]

        b_damage = row[39]
        d_damage = row[40]
        f_damage = row[41]
        i_damage = row[42]
        l_damage = row[43]
        m_damage = row[44]
        s_damage = row[45]

        b_pserve = row[46]
        d_pserve = row[47]
        f_pserve = row[48]
        i_pserve = row[49]
        l_pserve = row[50]
        m_pserve = row[51]
        s_pserve = row[52]

        b_resist = row[53]
        d_resist = row[54]
        f_resist = row[55]
        i_resist = row[56]
        l_resist = row[57]
        m_resist = row[58]
        s_resist = row[59]

        general = [
            f"{max_health} {emojis.HEALTH}",
            f"{max_mana} {emojis.MANA}",
            f"{ppc}% {emojis.POWER_PIP} Chance",
            f"{shad_rating} {emojis.SHADOW_PIP_STAT} Rating",
            f"{archmastery} {emojis.ARCHMASTERY} Rating",
            f"{outgoing}% {emojis.OUTGOING}",
            f"{incoming}% {emojis.INCOMING}",
            f"+{max_pips} {emojis.PIP}",
            f"+{max_power_pips} {emojis.POWER_PIP}"
        ]

        accuracy = [
            f"{b_acc}% {emojis.BALANCE} {emojis.ACCURACY}",
            f"{d_acc}% {emojis.DEATH} {emojis.ACCURACY}",
            f"{f_acc}% {emojis.FIRE} {emojis.ACCURACY}",
            f"{i_acc}% {emojis.ICE} {emojis.ACCURACY}",
            f"{l_acc}% {emojis.LIFE} {emojis.ACCURACY}",
            f"{m_acc}% {emojis.MYTH} {emojis.ACCURACY}",
            f"{s_acc}% {emojis.STORM} {emojis.ACCURACY}",
        ]

        pierce = [
            f"{b_ap}% {emojis.BALANCE} {emojis.PIERCE}",
            f"{d_ap}% {emojis.DEATH} {emojis.PIERCE}",
            f"{f_ap}% {emojis.FIRE} {emojis.PIERCE}",
            f"{i_ap}% {emojis.ICE} {emojis.PIERCE}",
            f"{l_ap}% {emojis.LIFE} {emojis.PIERCE}",
            f"{m_ap}% {emojis.MYTH} {emojis.PIERCE}",
            f"{s_ap}% {emojis.STORM} {emojis.PIERCE}",
        ]

        block = [
            f"{b_block} {emojis.BALANCE} {emojis.BLOCK}",
            f"{d_block} {emojis.DEATH} {emojis.BLOCK}",
            f"{f_block} {emojis.FIRE} {emojis.BLOCK}",
            f"{i_block} {emojis.ICE} {emojis.BLOCK}",
            f"{l_block} {emojis.LIFE} {emojis.BLOCK}",
            f"{m_block} {emojis.MYTH} {emojis.BLOCK}",
            f"{s_block} {emojis.STORM} {emojis.BLOCK}",
        ]

        crit = [
            f"{b_crit} {emojis.BALANCE} {emojis.CRIT}",
            f"{d_crit} {emojis.DEATH} {emojis.CRIT}",
            f"{f_crit} {emojis.FIRE} {emojis.CRIT}",
            f"{i_crit} {emojis.ICE} {emojis.CRIT}",
            f"{l_crit} {emojis.LIFE} {emojis.CRIT}",
            f"{m_crit} {emojis.MYTH} {emojis.CRIT}",
            f"{s_crit} {emojis.STORM} {emojis.CRIT}",
        ]

        damage = [
            f"{b_damage}% {emojis.BALANCE} {emojis.DAMAGE}",
            f"{d_damage}% {emojis.DEATH} {emojis.DAMAGE}",
            f"{f_damage}% {emojis.FIRE} {emojis.DAMAGE}",
            f"{i_damage}% {emojis.ICE} {emojis.DAMAGE}",
            f"{l_damage}% {emojis.LIFE} {emojis.DAMAGE}",
            f"{m_damage}% {emojis.MYTH} {emojis.DAMAGE}",
            f"{s_damage}% {emojis.STORM} {emojis.DAMAGE}",
        ]

        pserve = [
            f"{b_pserve} {emojis.BALANCE} {emojis.PIP_CONVERSION}",
            f"{d_pserve} {emojis.DEATH} {emojis.PIP_CONVERSION}",
            f"{f_pserve} {emojis.FIRE} {emojis.PIP_CONVERSION}",
            f"{i_pserve} {emojis.ICE} {emojis.PIP_CONVERSION}",
            f"{l_pserve} {emojis.LIFE} {emojis.PIP_CONVERSION}",
            f"{m_pserve} {emojis.MYTH} {emojis.PIP_CONVERSION}",
            f"{s_pserve} {emojis.STORM} {emojis.PIP_CONVERSION}",
        ]

        resist = [
            f"{b_resist}% {emojis.BALANCE} {emojis.RESIST}",
            f"{d_resist}% {emojis.DEATH} {emojis.RESIST}",
            f"{f_resist}% {emojis.FIRE} {emojis.RESIST}",
            f"{i_resist}% {emojis.ICE} {emojis.RESIST}",
            f"{l_resist}% {emojis.LIFE} {emojis.RESIST}",
            f"{m_resist}% {emojis.MYTH} {emojis.RESIST}",
            f"{s_resist}% {emojis.STORM} {emojis.RESIST}",
        ]

        embed = (
            discord.Embed(
                color=database.make_school_color(school),
                description="\n".join(general) or "\u200b",
            )
            .set_author(name=f"Level {level} {_SCHOOLS_STR[school-2]}", icon_url=database.translate_school(school).url)
            .add_field(name="Damage", value="\n".join(damage))
            .add_field(name="Resist", value="\n".join(resist))
            .add_field(name="Accuracy", value="\n".join(accuracy))
            .add_field(name="Critical", value="\n".join(crit))
            .add_field(name="Block", value="\n".join(block))
            .add_field(name="Pierce", value="\n".join(pierce))
            .add_field(name="Pip Conserve", value="\n".join(pserve))
        )

        return embed

    @app_commands.command(name="find", description="Finds a stat cap by level and school")
    async def find(
        self, 
        interaction: discord.Interaction, 
        level: int,
        school: Literal["Fire", "Ice", "Storm", "Myth", "Life", "Death", "Balance"],
    ):
        level = int(level/10)*10
        await interaction.response.defer()
        if type(interaction.channel) is PartialMessageable:
            logger.info("{} requested stat caps for '{}' '{}'", interaction.user.name, level, school)
        else:
            logger.info("{} requested stat caps for '{}' '{}' in channel #{} of {}", interaction.user.name, level, school, interaction.channel.name, interaction.guild.name)

        rows = await self.fetch_stat_cap(level=level, school=(_SCHOOLS_STR.index(school)+2))
    
        view = ItemView([await self.build_stat_cap_embed(row) for row in rows])
        await view.start(interaction)




async def setup(bot: TheBot):
    await bot.add_cog(StatCaps(bot))
