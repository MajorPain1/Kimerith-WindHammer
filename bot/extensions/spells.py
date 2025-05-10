from typing import List, Optional, Literal
from fuzzywuzzy import process, fuzz
from operator import attrgetter
import re
import os

import discord
from discord import app_commands, DMChannel, PartialMessageable
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

FIND_OBJECT_NAME_FROM_ID = """
SELECT * FROM spells
WHERE spells.template_id == ?
"""

FIND_MOB_OBJECT_NAME_FROM_ID = """
SELECT * FROM mobs
WHERE mobs.id == ?
"""

FIND_SPELLS_WITH_FILTER_QUERY = """
SELECT * FROM spells
INNER JOIN locale_en ON locale_en.id == spells.name
WHERE locale_en.data COLLATE NOCASE IN ({placeholders})
AND (? = 'Any' OR spells.school = ?)
AND (? = 'Any' OR spells.form = ?)
AND (? = -1 OR spells.rank = ?)
COLLATE NOCASE
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
    
    async def fetch_object_name_from_id(self, id: int) -> List[tuple]:
        async with self.bot.db.execute(FIND_OBJECT_NAME_FROM_ID, (id,)) as cursor:
            return await cursor.fetchall()
    
    async def fetch_mob_object_name_from_id(self, id: int) -> List[tuple]:
        async with self.bot.db.execute(FIND_MOB_OBJECT_NAME_FROM_ID, (id,)) as cursor:
            return await cursor.fetchall()
        
    async def fetch_spells_with_filter(self, spells: List[str], school: Optional[str] = "Any", kind: Optional[str] = "Any", rank: Optional[int] = -1, return_row=False):
        if isinstance(spells, str):
            spells = [spells]

        results = []
        
        school_val = (database._SCHOOLS_STR.index(school) + 2) if school != "Any" else None
        kind_val = database._SPELL_TYPES_STR.index(kind) if kind != "Any" else None
        for chunk in database.sql_chunked(spells, 900):  # Stay under SQLite's limit
            placeholders = database._make_placeholders(len(chunk))
            query = FIND_SPELLS_WITH_FILTER_QUERY.format(placeholders=placeholders)

            args = (
                *chunk,
                school, school_val,
                kind, kind_val,
                rank, rank
            )

            async with self.bot.db.execute(query, args) as cursor:
                rows = await cursor.fetchall()

            if return_row:
                results.extend(rows)
            else:
                results.extend(row[-1] for row in rows)

        return results
    
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

    async def fetch_real_spell_effects(self, spell: int):
        res = []
        async with self.bot.db.execute(
            "SELECT * FROM spell_effects WHERE spell_id == ?", (spell,)
        ) as cursor:
            async for row in cursor:
                res.append(row)
        
        res = sorted(res, key=lambda effect: effect[1])
        return res
    
    def replace_condition_with_emojis(self, string, use_blade_trap=False):
        target_full_pattern = r"(?i)\bnot Target School (Death|Fire|Ice|Life|Myth|Storm)\b" \
                    r"(?: and not Target School (?!\1)(Death|Fire|Ice|Life|Myth|Storm))" \
                    r"(?: and not Target School (?!\1|\2)(Death|Fire|Ice|Life|Myth|Storm))" \
                    r"(?: and not Target School (?!\1|\2|\3)(Death|Fire|Ice|Life|Myth|Storm))" \
                    r"(?: and not Target School (?!\1|\2|\3|\4)(Death|Fire|Ice|Life|Myth|Storm))" \
                    r"(?: and not Target School (?!\1|\2|\3|\4|\5)(Death|Fire|Ice|Life|Myth|Storm))"
        string = re.sub(target_full_pattern, f"{emojis.BALANCE}", string)
        caster_full_pattern = r"(?i)\bnot Caster School (Death|Fire|Ice|Life|Myth|Storm)\b" \
                    r"(?: and not Caster School (?!\1)(Death|Fire|Ice|Life|Myth|Storm))" \
                    r"(?: and not Caster School (?!\1|\2)(Death|Fire|Ice|Life|Myth|Storm))" \
                    r"(?: and not Caster School (?!\1|\2|\3)(Death|Fire|Ice|Life|Myth|Storm))" \
                    r"(?: and not Caster School (?!\1|\2|\3|\4)(Death|Fire|Ice|Life|Myth|Storm))" \
                    r"(?: and not Caster School (?!\1|\2|\3|\4|\5)(Death|Fire|Ice|Life|Myth|Storm))"
        string = re.sub(caster_full_pattern, f"{emojis.BALANCE}", string)
        string = string.replace(" School Fire", f" {emojis.FIRE}").replace(" School Storm", f" {emojis.STORM}").replace(" School Ice", f" {emojis.ICE}").replace(" School Myth", f" {emojis.MYTH}").replace(" School Life", f" {emojis.LIFE}").replace(" School Death", f" {emojis.DEATH}").replace(" School Balance", f" {emojis.BALANCE}")
        string = string.replace(" Shield", f" {emojis.WARD}").replace(" Weakness", f" {emojis.CURSE}").replace(" DOT", f" {emojis.DOT}").replace(" HOT", f" {emojis.HOT}").replace(" Negative Aura", f" {emojis.AURA_NEGATIVE}").replace(" Aura", f" {emojis.AURA}")
        
        if not use_blade_trap:
            string = string.replace(" Blade", f" {emojis.CHARM}").replace(" Trap", f" {emojis.JINX}")
        else:
            string = string.replace(" Blade", f" {emojis.BLADE}").replace(" Trap", f" {emojis.TRAP}")
            
        string = string.replace(" DamageOverTime", f" {emojis.DOT}").replace(" HealOverTime", f" {emojis.HOT}")
        string = string.replace(" Charm", f" {emojis.CHARM}/{emojis.CURSE}").replace(" Ward", f" {emojis.WARD}/{emojis.JINX}").replace(" OT", f" {emojis.DOT}/{emojis.HOT}")
        return string.replace(" on", "").replace(" has", "")

    def replace_consecutive_duplicates(self, input_string):
        # Split the input into lines
        lines = input_string.splitlines()
        result = []
        i = 0

        while i < len(lines):
            current_line = lines[i]
            count = 1

            # Check for consecutive duplicates
            while i + 1 < len(lines) and lines[i + 1] == current_line:
                count += 1
                i += 1

            # Add the line with the count if there are duplicates
            if count > 1 and current_line.strip() != "":
                result.append(f"{current_line} x{count}")
            else:
                result.append(current_line)
            
            # Move to the next line
            i += 1

        # Join the processed lines back into a string
        return "\n".join(result)

    def remove_index_from_string(self, text, index):
        return text[:index] + "@" + text[index+1:]
    
    def condense_conditionals(self, text):
        sections = text.split("\n\n")
        
        # CHROMATIC CONDENSER!
        conditionals = {}
        
        for section in sections:
            section: str
            
            raw_string = section.replace(f"{emojis.DEATH}", "@").replace(f"{emojis.FIRE}", "@").replace(f"{emojis.ICE}", "@").replace(f"{emojis.LIFE}", "@").replace(f"{emojis.MYTH}", "@").replace(f"{emojis.STORM}", "@")

            raw_string = raw_string.lstrip("\n")
            
            if raw_string in conditionals:
                conditionals[raw_string] = conditionals[raw_string]+1
            else:
                conditionals[raw_string] = 1
        
        indices_to_remove = []
        keys_seen = []
        for i, section in enumerate(sections):
            raw_string = section.replace(f"{emojis.DEATH}", "@").replace(f"{emojis.FIRE}", "@").replace(f"{emojis.ICE}", "@").replace(f"{emojis.LIFE}", "@").replace(f"{emojis.MYTH}", "@").replace(f"{emojis.STORM}", "@").lstrip("\n")
            if conditionals[raw_string] >= 6:
                if raw_string in keys_seen:
                    indices_to_remove.append(i)
                else:
                    keys_seen = raw_string
                    sections[i] = raw_string

        result = [value for idx, value in enumerate(sections) if idx not in indices_to_remove]

        reconstruct = []
        for section in result:
            if "Target @" in section:
                section = section.replace("Target @", f"{emojis.ELEMENTAL}/{emojis.SPIRIT}").replace("@", f"{emojis.CHROMATIC_TARGET}")
            if "Caster @" in section:
                section = section.replace("Caster @", f"{emojis.ELEMENTAL}/{emojis.SPIRIT}").replace("@", f"{emojis.CHROMATIC_CASTER}")
            reconstruct.append(section.replace(" Caster", "").replace(" Target", "").replace("@", f"{emojis.CHROMATIC_TARGET}"))
        
        return "\n\n".join(reconstruct)
    
    async def get_string_from_effect(self, effect, parent_is_x_pip=False, parent_is_convert=False):
        effect_id = effect[0]
        spell_id = effect[1]
        effect_class = effect[4]
        param = effect[5]
        disposition = effect[6]
        target = database.EffectTarget(effect[7])
        effect_type = database.SpellEffects(effect[8])
        heal_modifier = effect[9]
        rounds = effect[10]
        pip_num = effect[11]
        protected = bool(effect[12])
        rank = effect[13]
        school = database.translate_school(effect[14])
        condition = effect[15]
        
        new_line: str = ""
        
        if parent_is_x_pip:
            new_line += f"{rank} {emojis.PIP}: "
        elif parent_is_convert and rank != 0:
            new_line += f"{rank}: "
        
        match effect_type:
            case database.SpellEffects.absorb_damage:
                if protected:
                    new_line += f"{param} {school}{emojis.PABSORB}"
                else:
                    new_line += f"{param} {school}{emojis.ABSORB}"
                    
            case database.SpellEffects.absorb_heal:
                if protected:
                    new_line += f"{param} {emojis.HEART}{emojis.PABSORB}"
                else:
                    new_line += f"{param} {emojis.HEART}{emojis.ABSORB}"
                    
            case database.SpellEffects.add_combat_trigger_list:
                new_line += f"Add to Combat Trigger List"
            case database.SpellEffects.add_spell_to_deck:
                object_name = (await self.fetch_object_name_from_id(param))[0][3].decode("utf-8").replace("_", "\_")
                new_line += f"Add {object_name} To Deck"
            case database.SpellEffects.add_spell_to_hand:
                object_name = (await self.fetch_object_name_from_id(param))[0][3].decode("utf-8").replace("_", "\_")
                new_line += f"Add {object_name} To Hand"
            case database.SpellEffects.after_life:
                new_line += f"{param} {school}{emojis.HEART} {emojis.AFTERLIFE}"
            case database.SpellEffects.auto_pass:
                new_line += f"Auto Pass"
            case database.SpellEffects.backlash_damage:
                new_line += f"{school} Backlash"
            case database.SpellEffects.cloaked_charm:
                if protected:
                    new_line += f"{param}% {emojis.CLOAK}{school}{emojis.PCHARM}"
                else:
                    new_line += f"{param}% {emojis.CLOAK}{school}{emojis.CHARM}"
                
            case database.SpellEffects.cloaked_ward:
                if protected:
                    new_line += f"{param}% {emojis.CLOAK}{school}{emojis.PWARD}"
                else:
                    new_line += f"{param}% {emojis.CLOAK}{school}{emojis.WARD}"
                
            case database.SpellEffects.cloaked_ward_no_remove:
                if protected:
                    new_line += f"{param}% {emojis.CLOAK}{school}{emojis.PWARD} No Remove"
                else:
                    new_line += f"{param}% {emojis.CLOAK}{school}{emojis.WARD} No Remove"
                
            case database.SpellEffects.clue:
                new_line += f"Spy {param}{emojis.ROUNDS}"
            case database.SpellEffects.collect_essence:
                new_line += f"Extract"
            case database.SpellEffects.confusion:
                new_line += f"{param}% Confuse"
            case database.SpellEffects.crit_block:
                new_line += f"{param}% {school}{emojis.BLOCK}"
            case database.SpellEffects.crit_boost | database.SpellEffects.crit_boost_school_specific:
                new_line += f"{param}% {school}{emojis.CRIT}"
            case database.SpellEffects.damage:
                new_line += f"{param} {school}{emojis.DAMAGE}"
            case database.SpellEffects.damage_no_crit:
                new_line += f"{param} {school}{emojis.DAMAGE} No Crit"
            case database.SpellEffects.damage_over_time:
                if protected:
                    new_line += f"{param} {school}{emojis.PDOT}"
                else:
                    new_line += f"{param} {school}{emojis.DOT}"
                    
            case database.SpellEffects.damage_per_total_pip_power:
                new_line += f"{rounds} {school}{emojis.DAMAGE} per {emojis.ALL_ENEMIES}{emojis.PIP}"
            case database.SpellEffects.dampen:
                new_line += f"Max {param} {emojis.PIP}"
            case database.SpellEffects.deferred_damage:
                if protected:
                    new_line += f"{param} {school}{emojis.PBOMB}"
                else:
                    new_line += f"{param} {school}{emojis.BOMB}"
                    
            case database.SpellEffects.detonate_over_time:
                match disposition:
                    case 0:
                        new_line += f"Detonate {int(heal_modifier*100)}% {param} {emojis.DOT}/{emojis.HOT}"
                    case 1:
                        new_line += f"Activate {int(heal_modifier*100)}% {param} {emojis.HOT}"
                    case 2:
                        new_line += f"Detonate {int(heal_modifier*100)}% {param} {emojis.DOT}"
            
            case database.SpellEffects.dispel:
                new_line += f"{emojis.DISPEL}{school}"
            case database.SpellEffects.dispel_block:
                new_line += f"{emojis.DISPEL} Block"
            case database.SpellEffects.divide_damage:
                new_line += f"Divide {param} {school}{emojis.DAMAGE}"
            case database.SpellEffects.exit_combat:
                new_line += f"Exit Combat"
            case database.SpellEffects.force_targetable:
                new_line += f"Force Targetable"
            case database.SpellEffects.heal | database.SpellEffects.heal_by_ward | database.SpellEffects.heal_percent:
                new_line += f"{param} {school}{emojis.HEART}"
            case database.SpellEffects.heal_over_time:
                new_line += f"{param} {school}{emojis.HOT}"
            case database.SpellEffects.heal_percent | database.SpellEffects.max_health_heal:
                new_line += f"{param}% {school}{emojis.HEART}"
            case database.SpellEffects.instant_kill:
                new_line += f"{param} {school} Instant Kill"
            case database.SpellEffects.invalid_spell_effect:
                new_line += f"Invalid Spell Effect"
            case database.SpellEffects.kill_creature:
                mob_name = (await self.fetch_mob_object_name_from_id(param))[0][2].decode("utf-8")
                new_line += f"Kill {mob_name}"
            case database.SpellEffects.make_targetable:
                new_line += f"Make Targetable"
            case database.SpellEffects.max_health_damage:
                new_line += f"{param}% Max HP {school}{emojis.DAMAGE}"
            case database.SpellEffects.maximum_incoming_damage:
                new_line += f"{param} Equalize"
            case database.SpellEffects.mind_control:
                new_line += f"Beguile {param}{emojis.ROUNDS}"
            case database.SpellEffects.modify_accuracy | database.SpellEffects.modify_card_accuracy | database.SpellEffects.modify_card_outgoing_accuracy:
                new_line += f"{param}% {school}{emojis.ACCURACY}"
            case database.SpellEffects.modify_card_armor_piercing | database.SpellEffects.modify_card_outgoing_armor_piercing:
                new_line += f"+{param}% {school}{emojis.PIERCE}"
            case database.SpellEffects.modify_card_cloak:
                new_line += f"{emojis.CLOAK}"
            case database.SpellEffects.modify_card_damage:
                new_line += f"+{param} {emojis.DAMAGE}"
            case database.SpellEffects.modify_card_damage_by_rank:
                new_line += f"+{param} per {emojis.PIP} (MAX: {rounds})"
            case database.SpellEffects.modify_card_heal:
                new_line += f"+{param} {emojis.HEART}"
            case database.SpellEffects.modify_card_incoming_damage:
                match disposition:
                    case 0 | 1:
                        new_line += f"{param}% {emojis.WARD}"
                    case 2:
                        new_line += f"+{param}% {emojis.TRAP}"
            
            case database.SpellEffects.modify_card_mutation:
                object_name = await self.fetch_object_name_from_id(param)
                new_line += f"Mutate to {object_name}"
            case database.SpellEffects.modify_card_rank:
                new_line += f"Modify Rank by {param} {emojis.PIP}"
            case database.SpellEffects.modify_hate:
                if param > 0:
                    new_line += f"+{param} Hate"
                elif param < 0:
                    new_line += f"{param} Hate"
                else:
                    new_line += f"Devour"
            
            case database.SpellEffects.modify_incoming_armor_piercing:
                if rounds == 0 and target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.PIERCE}{emojis.TRAP}"
                    else:
                        new_line += f"{param}% {school}{emojis.PIERCE}{emojis.WARD}"
                elif target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.PIERCE}{emojis.AURA_NEGATIVE}"
                    else:
                        new_line += f"{param}% {school}{emojis.PIERCE}{emojis.AURA}"
                else:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.PIERCE}"
                    else:
                        new_line += f"{param}% {school}{emojis.PIERCE}"
            
            case database.SpellEffects.modify_incoming_damage:
                if rounds == 0 and target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.TRAP}"
                    else:
                        new_line += f"{param}% {school}{emojis.SHIELD}"
                elif target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.AURA_NEGATIVE}"
                    else:
                        new_line += f"{param}% {school}{emojis.AURA}"
                else:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.DAMAGE}"
                    else:
                        new_line += f"{param}% {school}{emojis.DAMAGE}"
            
            case database.SpellEffects.modify_incoming_damage_flat:
                if rounds == 0 and target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param} {school}{emojis.TRAP}"
                    else:
                        new_line += f"{param} {school}{emojis.SHIELD}"
                elif target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param} {school}{emojis.AURA_NEGATIVE}"
                    else:
                        new_line += f"{param} {school}{emojis.AURA}"
                else:
                    if param >= 0:
                        new_line += f"+{param} {school}{emojis.FLAT_DAMAGE}"
                    else:
                        new_line += f"{param} {school}{emojis.FLAT_DAMAGE}"
            
            case database.SpellEffects.modify_incoming_damage_over_time:
                if rounds == 0 and target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.DOT}{emojis.JINX}"
                    else:
                        new_line += f"{param}% {school}{emojis.DOT}{emojis.WARD}"
                elif target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.DOT}{emojis.AURA_NEGATIVE}"
                    else:
                        new_line += f"{param}% {school}{emojis.DOT}{emojis.AURA}"
                else:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.DOT}{emojis.DAMAGE}"
                    else:
                        new_line += f"{param}% {school}{emojis.DOT}{emojis.DAMAGE}"
            
            case database.SpellEffects.modify_incoming_damage_type:
                new_line += f"Convert {school} to {database.school_prism_values[param]} {emojis.JINX}"
            case database.SpellEffects.modify_incoming_heal:
                if rounds == 0 and target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.HEART}{emojis.JINX}"
                    else:
                        new_line += f"{param}% {school}{emojis.HEART}{emojis.JINX}"
                elif target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.HEART}{emojis.AURA}"
                    else:
                        new_line += f"{param}% {school}{emojis.HEART}{emojis.AURA_NEGATIVE}"
                else:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.HEART}"
                    else:
                        new_line += f"{param}% {school}{emojis.HEART}"
            
            case database.SpellEffects.modify_incoming_heal_flat:
                if rounds == 0:
                    if param >= 0:
                        new_line += f"+{param} {school}{emojis.HEART}"
                    else:
                        new_line += f"{param} {school}{emojis.HEART}"
                else:
                    if param >= 0:
                        new_line += f"+{param} {school}{emojis.HEART}{emojis.AURA}"
                    else:
                        new_line += f"{param} {school}{emojis.HEART}{emojis.AURA_NEGATIVE}"
            
            case database.SpellEffects.modify_incoming_heal_over_time:
                if rounds == 0 and target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.HOT}{emojis.JINX}"
                    else:
                        new_line += f"{param}% {school}{emojis.HOT}{emojis.JINX}"
                elif target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.HOT}{emojis.AURA}"
                    else:
                        new_line += f"{param}% {school}{emojis.HOT}{emojis.AURA_NEGATIVE}"
                else:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.HOT}"
                    else:
                        new_line += f"{param}% {school}{emojis.HOT}"
            
            case database.SpellEffects.modify_outgoing_armor_piercing:
                if rounds == 0 and target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.PIERCE}{emojis.CHARM}"
                    else:
                        new_line += f"{param}% {school}{emojis.PIERCE}{emojis.CURSE}"
                elif target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.PIERCE}{emojis.AURA}"
                    else:
                        new_line += f"{param}% {school}{emojis.PIERCE}{emojis.AURA_NEGATIVE}"
                else:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.PIERCE}"
                    else:
                        new_line += f"{param}% {school}{emojis.PIERCE}"
            
            case database.SpellEffects.modify_outgoing_damage:
                if rounds == 0 and target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.BLADE}"
                    else:
                        new_line += f"{param}% {school}{emojis.WEAKNESS}"
                elif target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.DAMAGE}{emojis.AURA}"
                    else:
                        new_line += f"{param}% {school}{emojis.DAMAGE}{emojis.AURA_NEGATIVE}"
                else:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.DAMAGE}"
                    else:
                        new_line += f"{param}% {school}{emojis.DAMAGE}"
            
            case database.SpellEffects.modify_outgoing_damage_flat:
                if rounds == 0 and target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param} {school}{emojis.BLADE}"
                    else:
                        new_line += f"{param} {school}{emojis.WEAKNESS}"
                elif target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param} {school}{emojis.DAMAGE}{emojis.AURA}"
                    else:
                        new_line += f"{param} {school}{emojis.DAMAGE}{emojis.AURA_NEGATIVE}"
                else:
                    if param >= 0:
                        new_line += f"+{param} {school}{emojis.FLAT_DAMAGE}"
                    else:
                        new_line += f"{param} {school}{emojis.FLAT_DAMAGE}"
            
            case database.SpellEffects.modify_outgoing_damage_type:
                new_line += f"Convert {school} to {database.school_prism_values[param]} {emojis.CHARM}"
            case database.SpellEffects.modify_outgoing_heal:
                if rounds == 0 and target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.HEART}{emojis.CHARM}"
                    else:
                        new_line += f"{param}% {school}{emojis.HEART}{emojis.CURSE}"
                elif target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.HEART}{emojis.AURA}"
                    else:
                        new_line += f"{param}% {school}{emojis.HEART}{emojis.AURA_NEGATIVE}"
                else:
                    if param >= 0:
                        new_line += f"+{param}% {school}{emojis.HEART}"
                    else:
                        new_line += f"{param}% {school}{emojis.HEART}"
                        
            case database.SpellEffects.modify_outgoing_heal_flat:
                if rounds == 0 and target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param} {school}{emojis.HEART}{emojis.CHARM}"
                    else:
                        new_line += f"{param} {school}{emojis.HEART}{emojis.CURSE}"
                elif target != database.EffectTarget.target_global:
                    if param >= 0:
                        new_line += f"+{param} {school}{emojis.HEART}{emojis.AURA}"
                    else:
                        new_line += f"{param} {school}{emojis.HEART}{emojis.AURA_NEGATIVE}"
                else:
                    if param >= 0:
                        new_line += f"+{param} {school}{emojis.HEART}"
                    else:
                        new_line += f"{param} {school}{emojis.HEART}"
            
            case database.SpellEffects.modify_over_time_duration:
                match disposition:
                    case 0 | 1:
                        new_line += f"Add {emojis.HOT}"
                    case 2:
                        new_line += f"Add {emojis.DOT}"
            
            case database.SpellEffects.modify_pip_round_rate:
                if param >= 0:
                    new_line += f"+{param} {emojis.PIP} Gain Per Round"
                else:
                    new_line += f"{param} {emojis.PIP} Gain Per Round"
            
            case database.SpellEffects.modify_pips:
                if param >= 0:
                    new_line += f"+{param} {emojis.PIP}"
                else:
                    new_line += f"{param} {emojis.PIP}"
            
            case database.SpellEffects.modify_power_pip_chance:
                if param >= 0:
                    new_line += f"+{param}% {emojis.POWER_PIP} Chance"
                else:
                    new_line += f"{param}% {emojis.POWER_PIP} Chance"
            
            case database.SpellEffects.modify_power_pips:
                if param >= 0:
                    new_line += f"+{param} {emojis.POWER_PIP}"
                else:
                    new_line += f"{param} {emojis.POWER_PIP}"
            
            case database.SpellEffects.modify_rank:
                if param >= 0:
                    new_line += f"+{param} {school} Rank"
                else:
                    new_line += f"{param} {school} Rank"
            
            case database.SpellEffects.modify_school_pips:
                if param >= 0:
                    new_line += f"+{param} {school}{emojis.POWER_PIP}"
                else:
                    new_line += f"{param} {school}{emojis.POWER_PIP}"
            
            case database.SpellEffects.modify_shadow_creature_level:
                if param >= 0:
                    new_line += f"+{param} Shadow Creature Level"
                else:
                    new_line += f"{param} Shadow Creature Level"
            
            case database.SpellEffects.modify_shadow_pips:
                if param >= 0:
                    new_line += f"+{param} {emojis.SHADOW_PIP}"
                else:
                    new_line += f"{param} {emojis.SHADOW_PIP}"
            
            case database.SpellEffects.pacify:
                new_line += f"Pacify"
            case database.SpellEffects.pip_conversion:
                if param >= 0:
                    new_line += f"+{param} {emojis.PIP} from Incoming Rank {pip_num} Spells"
                else:
                    new_line += f"{param} {emojis.PIP} from Incoming Rank {pip_num} Spells"
            case database.SpellEffects.polymorph:
                new_line += f"Polymorph into {param}"
            case database.SpellEffects.power_pip_conversion:
                if param >= 0:
                    new_line += f"+{param} {emojis.POWER_PIP} from Incoming Rank {pip_num} Spells"
                else:
                    new_line += f"{param} {emojis.POWER_PIP} from Incoming Rank {pip_num} Spells"
            case database.SpellEffects.protect_card_beneficial:
                new_line += f"Protect {emojis.CHARM}"
            case database.SpellEffects.protect_card_harmful:
                new_line += f"Protect {emojis.JINX}"
            case database.SpellEffects.push_charm:
                new_line += f"Push {param} {emojis.CURSE}"
            case database.SpellEffects.push_over_time:
                new_line += f"Push {param} {emojis.DOT}"
            case database.SpellEffects.push_ward:
                new_line += f"Push {param} {emojis.JINX}"
            case database.SpellEffects.reduce_over_time:
                new_line += f"{param} {emojis.DOT}{emojis.ROUNDS}"
            case database.SpellEffects.remove_aura:
                new_line += f"Remove {emojis.AURA}"
            case database.SpellEffects.remove_charm:
                match disposition:
                    case 0 | 1:
                        new_line += f"Remove {param} {emojis.CHARM}"
                    case 2:
                        new_line += f"Remove {param} {emojis.CURSE}"
            case database.SpellEffects.remove_combat_trigger_list:
                new_line += "Remove Combat Trigger List"
            case database.SpellEffects.remove_over_time:
                match disposition:
                    case 0 | 1:
                        new_line += f"Remove {param} {emojis.HOT}"
                    case 2:
                        new_line += f"Remove {param} {emojis.DOT}"
            case database.SpellEffects.remove_stun_block:
                new_line += f"Remove {emojis.STUN_BLOCK}"
            case database.SpellEffects.remove_ward:
                match disposition:
                    case 0 | 1:
                        new_line += f"Remove {param} {emojis.WARD}"
                    case 2:
                        new_line += f"Remove {param} {emojis.JINX}"
            case database.SpellEffects.reshuffle:
                new_line += "Reshuffle"
            case database.SpellEffects.resume_pips:
                new_line += "Resume Pips"
            case database.SpellEffects.select_shadow_creature_attack_target:
                new_line += "Select Shadow Creature Attack Target"
            case database.SpellEffects.shadow_decrement_turn:
                new_line += "Shadow Decrement Turn"
            case database.SpellEffects.spawn_creature | database.SpellEffects.summon_creature:
                mob_name = (await self.fetch_mob_object_name_from_id(param))[0][2].decode("utf-8").replace("_", "\_")
                new_line += f"Summon {mob_name}"
            case database.SpellEffects.steal_charm:
                match disposition:
                    case 0 | 1:
                        new_line += f"Steal {param} {emojis.CHARM}"
                    case 2:
                        new_line += f"Push {param} {emojis.CURSE}"
            case database.SpellEffects.steal_health:
                new_line += f"{param} {school}{emojis.STEAL} ({heal_modifier*100}%)"
            case database.SpellEffects.steal_over_time:
                match disposition:
                    case 0 | 1:
                        new_line += f"Steal {param} {emojis.HOT}"
                    case 2:
                        new_line += f"Push {param} {emojis.DOT}"
            case database.SpellEffects.steal_ward:
                match disposition:
                    case 0 | 1:
                        new_line += f"Steal {param} {emojis.WARD}"
                    case 2:
                        new_line += f"Push {param} {emojis.JINX}"
            case database.SpellEffects.stop_auto_pass:
                new_line += "Stop Auto Pass"
            case database.SpellEffects.stop_vanish:
                new_line += "Stop Vanish"
            case database.SpellEffects.stun:
                new_line += f"{emojis.STUN} {param}{emojis.ROUNDS}"
            case database.SpellEffects.stun_block:
                new_line += f"{param} {emojis.STUN_BLOCK}"
            case database.SpellEffects.suspend_pips:
                new_line += "Suspend Pips"
            case database.SpellEffects.swap_all:
                new_line += "Swap All"
            case database.SpellEffects.swap_charm:
                match disposition:
                    case 0:
                        new_line += f"Swap {emojis.CHARM}/{emojis.CURSE}"
                    case 1:
                        new_line += f"Swap {emojis.CHARM}"
                    case 2:
                        new_line += f"Swap {emojis.CURSE}"
            case database.SpellEffects.swap_over_time:
                match disposition:
                    case 0:
                        new_line += f"Swap {emojis.DOT}/{emojis.HOT}"
                    case 1:
                        new_line += f"Swap {emojis.HOT}"
                    case 2:
                        new_line += f"Swap {emojis.DOT}"
            case database.SpellEffects.swap_ward:
                match disposition:
                    case 0:
                        new_line += f"Swap {emojis.WARD}/{emojis.JINX}"
                    case 1:
                        new_line += f"Swap {emojis.WARD}"
                    case 2:
                        new_line += f"Swap {emojis.JINX}"
            case database.SpellEffects.taunt:
                new_line += f"Taunt"
            case database.SpellEffects.un_polymorph:
                new_line += f"Unpolymorph"
            case database.SpellEffects.untargetable:
                new_line += f"Untargetable"
            case database.SpellEffects.vanish:
                new_line += f"Vanish"

        no_round_list = [
            database.SpellEffects.max_health_damage, 
            database.SpellEffects.damage_no_crit, 
            database.SpellEffects.damage, 
            database.SpellEffects.clue, 
            database.SpellEffects.damage_per_total_pip_power, 
            database.SpellEffects.detonate_over_time, 
            database.SpellEffects.heal_by_ward, 
            database.SpellEffects.mind_control, 
            database.SpellEffects.modify_card_damage_by_rank, 
            database.SpellEffects.stun
        ]
        if rounds > 0 and not effect_type in no_round_list:
            new_line += f" {rounds}{emojis.ROUNDS}"
            
        remove_all_list = [
            database.SpellEffects.push_charm,
            database.SpellEffects.push_converted_charm,
            database.SpellEffects.push_converted_over_time,
            database.SpellEffects.push_converted_ward,
            database.SpellEffects.push_over_time,
            database.SpellEffects.push_ward,
            database.SpellEffects.remove_aura,
            database.SpellEffects.remove_charm,
            database.SpellEffects.remove_converted_charm,
            database.SpellEffects.remove_converted_over_time,
            database.SpellEffects.remove_converted_ward,
            database.SpellEffects.remove_over_time,
            database.SpellEffects.remove_stun_block,
            database.SpellEffects.remove_ward,
            database.SpellEffects.steal_charm,
            database.SpellEffects.steal_converted_charm,
            database.SpellEffects.steal_converted_over_time,
            database.SpellEffects.steal_converted_ward,
            database.SpellEffects.steal_ward,
            database.SpellEffects.steal_over_time,
            database.SpellEffects.detonate_over_time,
        ]    
        if param == -1 and effect_type in remove_all_list:
            new_line = new_line.replace("-1", "all")
            
        if parent_is_convert and rank == 0:
            new_line = new_line.replace("+", "1: ")
            new_line = new_line.replace("% ", f"% of effect to ")
        
        match target:
            case database.EffectTarget.enemy_team_all_at_once | database.EffectTarget.enemy_team:
                new_line += f" {emojis.ALL_ENEMIES_SQUARE}"
            case database.EffectTarget.spell | database.EffectTarget.specific_spells:
                new_line += f" {emojis.ENCHANTMENT}"
            case database.EffectTarget.self:
                new_line += f" {emojis.SELF}"
            case database.EffectTarget.enemy_single:
                new_line += f" {emojis.ALL_ENEMIES}"
            case database.EffectTarget.friendly_team | database.EffectTarget.friendly_team_all_at_once:
                new_line += f" {emojis.ALL_FRIENDS_SQUARE}"
            case database.EffectTarget.friendly_single:
                new_line += f" {emojis.ALL_FRIENDS}"
            case database.EffectTarget.target_global:
                new_line += f" {emojis.GLOBAL}"
            case database.EffectTarget.minion:
                new_line += f" {emojis.MINION}"
            case database.EffectTarget.multi_target_enemy:
                new_line += f" {emojis.ALL_ENEMIES_SELECT}"
            case database.EffectTarget.multi_target_friendly:
                new_line += f" {emojis.ALL_FRIENDS_SELECT}"
        
        if effect_type != 0:
            return new_line
        else:
            return ""
    
    async def recursive_generate_effect_string(self, spell_effects, effect_string, nested_level=0, parent_is_x_pip=False, parent_is_convert=False, parent_id=-1):
        for effect in spell_effects:
            if effect[2] != parent_id:
                continue
            
            effect_id = effect[0]
            effect_class = effect[4]
            effect_type = database.SpellEffects(effect[8])
            condition = effect[15]

            if effect_type != database.SpellEffects.invalid_spell_effect and effect_type != database.SpellEffects.shadow_self and effect_type != database.SpellEffects.convert_hanging_effect:
                new_line = await self.get_string_from_effect(effect, parent_is_x_pip=parent_is_x_pip, parent_is_convert=parent_is_convert)
                effect_string.append(f"{new_line}\n")
            
            match effect_class:
                case 0:
                    await self.recursive_generate_effect_string(spell_effects, effect_string, nested_level+1, parent_id=effect_id)
                
                case 3 | 5:
                    await self.recursive_generate_effect_string(spell_effects, effect_string, nested_level, parent_id=effect_id)
                
                case 1:
                    effect_string.append(f"\nRandom:\n")
                    await self.recursive_generate_effect_string(spell_effects, effect_string, nested_level+1, parent_id=effect_id)
                    effect_string.append("\n")
                
                case 2:
                    effect_string.append(f"\nVariable:\n")
                    await self.recursive_generate_effect_string(spell_effects, effect_string, nested_level+1, parent_is_x_pip=True, parent_id=effect_id)
                    effect_string.append("\n")
                    
                case 4:
                    effect_string.append(f"\n{self.replace_condition_with_emojis(condition)}:\n")
                    await self.recursive_generate_effect_string(spell_effects, effect_string, nested_level+1, parent_id=effect_id)
                    effect_string.append("\n")
                    
                case 6:
                    effect_string.append(f"\n{self.replace_condition_with_emojis(condition, use_blade_trap=True)}:\n")
                    await self.recursive_generate_effect_string(spell_effects, effect_string, nested_level+1, parent_is_convert=True, parent_id=effect_id)
                    effect_string.append("\n")
                    

    async def generate_spell_effects_description(self, spell_effects):
        ret_list = []
        await self.recursive_generate_effect_string(spell_effects, ret_list)
        return "".join(ret_list)

    def parse_description(self, description, effects: List[tuple]) -> str:
        description = re.sub(r'#-?\d+:', '', description)
        description = re.sub("<[^>]*>", "", description)
        description = re.sub(r"\{[^{}]*\}", "", description)
        description = re.sub(r"%%", "%", description)

        for variable in re.findall(r"\$([\w:]+?)(\d*)\$", description):
            markdown_variable = variable[0]
            index = variable[1]
            actual = variable[0] + variable[1]

            if index:
                index = int(index) - 1
            else:
                index = 0

            if index > len(effects):
                index = len(effects) - 1


            match markdown_variable:
                case "eA" | "eAPerPip" | "eAPerPipAll":
                    if actual == "eA1":
                        description = description.replace(f'${actual}$', "")
                    elif index >= len(effects):
                        description = description.replace(f'${actual}$', "")
                    else:
                        description = description.replace(f'${actual}$', f"{effects[index][0]}")

                case "eAMul":
                    description = description.replace(f'${actual}$', f"50")

                case "eAMax":
                    description = description.replace(f'${actual}$', f"{effects[index][2]}")

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

                case "Gambit" | "Clear" | "Remove" | "Steal" | "Swap" | "Take" | "Echo" | "Detonate" | "or" | ":" | "/" | "if" | "Push":
                    description = description = description.replace(f'${actual}$', f"{actual}")

                case _:
                    description = description.replace(f'${actual}$', f"{database.translate_type_emoji(markdown_variable)}")


        return description.replace("\\n", "\n").replace("\\r", "\r")
        
    async def build_spell_embed(self, row, show_spell_effects=False):
        spell_id = row[1]
        real_name = row[3].decode("utf-8")
        image_file = row[4]
        accuracy = row[5]
        energy = row[6]
        school = row[7]
        description = row[8]
        type_name = row[9]
        pve = row[10]
        pvp = row[11]
        levelreq = row[12]

        rank = row[13]
        x_pips = row[14]
        shadow_pips = row[15] * f"{emojis.SHADOW_PIP}"
        fire_pips = row[16] * f"{emojis.FIRE}"
        ice_pips = row[17] * f"{emojis.ICE}"
        storm_pips = row[18] * f"{emojis.STORM}"
        myth_pips = row[19] * f"{emojis.MYTH}"
        life_pips = row[20] * f"{emojis.LIFE}"
        death_pips = row[21] * f"{emojis.DEATH}"
        balance_pips = row[22] * f"{emojis.BALANCE}"

        if x_pips:
            rank = "X"

        add_plus_sign = "+ " * any([shadow_pips, fire_pips, ice_pips, storm_pips, myth_pips, life_pips, death_pips, balance_pips])
        pip_count = f"Rank {rank} {add_plus_sign}{shadow_pips}{fire_pips}{ice_pips}{storm_pips}{myth_pips}{life_pips}{death_pips}{balance_pips}"



        spell_name = row[-1]

        parsed_description = ""
        if show_spell_effects:
            spell_effects = await self.fetch_real_spell_effects(spell_id)
            parsed_description = self.condense_conditionals(await self.generate_spell_effects_description(spell_effects)).replace(" Caster", "").replace(" Target", "").replace("\n\n\n", "\n\n")
            parsed_description = self.replace_consecutive_duplicates(parsed_description)
            
            #print(parsed_description)
            #print(len(parsed_description))
        else:
            effects = await self.fetch_spell_effects(spell_id)

            if not effects:
                effects.append((0, 0, 0))
                
            raw_description = await self.fetch_description(description)
            if raw_description:
                while type(raw_description) != str:
                    raw_description = raw_description[0]

                parsed_description = self.parse_description(raw_description, effects)
            else:
                parsed_description = "Description Not Found"

        if school == 12:
            try:
                type_string = database.GARDENING_TYPES[type_name]
            except IndexError:
                type_string = database._SPELL_TYPES[type_name]
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


        
        if pve and not pvp:
            pve_or_pvp_emoji = emojis.NO_PVP
        elif pvp and not pve:
            pve_or_pvp_emoji = emojis.PVP_ONLY
        elif pvp and pve:
            pve_or_pvp_emoji = emojis.NO_COMBAT
        else:
            pve_or_pvp_emoji = None
        
        embed = (
            discord.Embed(
                title=pip_count,
                color=database.make_school_color(school),
                description=parsed_description or "\u200b",
            )
            .set_author(name=f"{spell_name}\n({real_name}: {spell_id})", icon_url=database.translate_school(school).url)
            .add_field(name=accuracy_field, value="")
            .add_field(name=f"Type {type_string}", value="")
        )

        if levelreq != 0:
            embed.add_field(name=f"{levelreq} {emojis.LEVEL_RESTRICTION}", value="")

        if pve_or_pvp_emoji != None:
            embed.add_field(name=f"{pve_or_pvp_emoji}", value="")

        discord_file = None
        if image_file:
            try:
                image_name = (image_file.split("|")[-1]).split(".")[0]
                png_file = f"{image_name}.png"
                png_name = png_file.replace(" ", "")
                file_path = os.path.join("PNG_Images", png_name)
                discord_file = discord.File(file_path, filename=png_name)
                embed.set_thumbnail(url=f"attachment://{png_name}")
            except:
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
        use_object_name: Optional[bool] = False,
        show_spell_effects: Optional[bool] = False
    ):
        await interaction.response.defer()
        if type(interaction.channel) is DMChannel or type(interaction.channel) is PartialMessageable:
            logger.info("{} requested spell '{}'", interaction.user.name, name)
        else:
            logger.info("{} requested spell '{}' in channel #{} of {}", interaction.user.name, name, interaction.channel.name, interaction.guild.name)

        if use_object_name:
            rows = await self.fetch_object_name(name)
            if not rows:
                embed = discord.Embed(description=f"No spells with object name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
                await interaction.followup.send(embed=embed)
                
        else:
            rows = await self.fetch_spells_with_filter(name, school, kind, rank, return_row=True)
            if not rows:
                filtered_rows = await self.fetch_spells_with_filter(self.bot.spell_list, school, kind, rank, return_row=True)
                closest_rows = [(row, fuzz.token_set_ratio(name, row[-1]) + fuzz.ratio(name, row[-1])) for row in filtered_rows]
                closest_rows = sorted(closest_rows, key=lambda x: x[1], reverse=True)
                closest_rows = list(zip(*closest_rows))[0]
                
                rows = await self.fetch_spells_with_filter(closest_rows[0][-1], school, kind, rank, return_row=True)

                if rows:
                    logger.info("Failed to find '{}' instead searching for {}", name, closest_rows[0][-1])

        if rows:
            embeds = [await self.build_spell_embed(row, show_spell_effects=show_spell_effects) for row in rows]
            sorted_embeds = sorted(embeds, key=lambda embed: embed[0].author.name)
            unzipped_embeds, unzipped_images = list(zip(*sorted_embeds))
            view = ItemView(unzipped_embeds, files=unzipped_images)
            await view.start(interaction)
        elif not use_object_name:
            logger.info("Failed to find '{}'", name)
            embed = discord.Embed(description=f"No spells with name {name} found.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)
            await interaction.followup.send(embed=embed)

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
        if type(interaction.channel) is DMChannel or type(interaction.channel) is PartialMessageable:
            logger.info("{} searched for spells that contain '{}'", interaction.user.name, name)
        else:
            logger.info("{} searched for spells that contain '{}' in channel #{} of {}", interaction.user.name, name, interaction.channel.name, interaction.guild.name)

        spells_containing_name = []
        for spell in self.bot.spell_list:
            spell: str

            if name == '*' or name.lower() in spell.lower():
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
            embed = discord.Embed(description=f"Unable to find {name}.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)

            await interaction.followup.send(embed=embed)

        
        



async def setup(bot: TheBot):
    await bot.add_cog(Spells(bot))
