from typing import List, Optional, Literal
from fuzzywuzzy import process, fuzz
from operator import attrgetter
import re

import discord
from discord import app_commands, PartialMessageable
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

    async def fetch_real_spell_effects(self, spell: int):
        res = []
        async with self.bot.db.execute(
            "SELECT * FROM spell_effects WHERE spell_id == ?", (spell,)
        ) as cursor:
            async for row in cursor:
                res.append(row)
        
        res = sorted(res, key=lambda effect: effect[1])
        return res
    
    def replace_condition_with_emojis(self, string):
        target_full_pattern = r"(?i)\bnot Target School (Death|Fire|Ice|Life|Myth|Storm)\b" \
            r"(?: and not Target School (?!\1)(Death|Fire|Ice|Life|Myth|Storm))*" \
            r"(?: and not Target School (?!.*\2\b)(Death|Fire|Ice|Life|Myth|Storm))*" \
            r"(?: and not Target School (?!.*\3\b)(Death|Fire|Ice|Life|Myth|Storm))*" \
            r"(?: and not Target School (?!.*\4\b)(Death|Fire|Ice|Life|Myth|Storm))*" \
            r"(?: and not Target School (?!.*\5\b)(Death|Fire|Ice|Life|Myth|Storm))*"
        string = re.sub(target_full_pattern, f"{emojis.BALANCE}", string)
        caster_full_pattern = r"(?i)\bnot Caster School (Death|Fire|Ice|Life|Myth|Storm)\b" \
            r"(?: and not Caster School (?!\1)(Death|Fire|Ice|Life|Myth|Storm))*" \
            r"(?: and not Caster School (?!.*\2\b)(Death|Fire|Ice|Life|Myth|Storm))*" \
            r"(?: and not Caster School (?!.*\3\b)(Death|Fire|Ice|Life|Myth|Storm))*" \
            r"(?: and not Caster School (?!.*\4\b)(Death|Fire|Ice|Life|Myth|Storm))*" \
            r"(?: and not Caster School (?!.*\5\b)(Death|Fire|Ice|Life|Myth|Storm))*"
        string = re.sub(caster_full_pattern, f"{emojis.BALANCE}", string)
        string = string.replace(" School Fire", f" {emojis.FIRE}").replace(" School Storm", f" {emojis.STORM}").replace(" School Ice", f" {emojis.ICE}").replace(" School Myth", f" {emojis.MYTH}").replace(" School Life", f" {emojis.LIFE}").replace(" School Death", f" {emojis.DEATH}")
        string = string.replace(" Blade", f" {emojis.CHARM}").replace(" Shield", f" {emojis.WARD}").replace(" Weakness", f" {emojis.CURSE}").replace(" Trap", f" {emojis.JINX}").replace(" DOT", f" {emojis.DOT}").replace(" HOT", f" {emojis.HOT}").replace(" Aura", f" {emojis.AURA}").replace(" Negative Aura", f" {emojis.AURA_NEGATIVE}")
        string = string.replace(" DamageOverTime", f" {emojis.DOT}").replace(" HealOverTime", f" {emojis.HOT}")
        return string.replace(" Caster", "").replace(" Target", "").replace(" on", "").replace(" has", "")

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
    
    def condense_conditionals(self, text): # CHROMATIC CONDENSER!
        sections = text.split("\n\n")
        if len(sections) <= 17:
            return text
        
        conditionals = {}
        
        for section in sections:
            pass
        
        print(conditionals)
        result = [(key, conditionals[key]) for key in conditionals]
        print(result)
        reconstruct = []
        
        for section in result:
            reconstruct.append(section[1].replace("@", section[0]))
        
        return "\n\n".join(reconstruct)
    
    async def recursive_generate_effect_string(self, spell_effects, effect_string, nested_level=0, parent_is_x_pip=False, parent_id=-1):
        for effect in spell_effects:
            if effect[2] != parent_id:
                continue
            
            effect_id = effect[0]
            spell_id = effect[1]
            effect_class = effect[4]
            param = effect[5]
            disposition = effect[6]
            target = effect[7]
            effect_type = effect[8]
            heal_modifier = effect[9]
            rounds = effect[10]
            pip_num = effect[11]
            protected = bool(effect[12])
            rank = effect[13]
            school = database.translate_school(effect[14])
            condition = effect[15]
            
            new_line = ""
            
            if parent_is_x_pip:
                new_line += f"{rank} {emojis.PIP}: "
            match effect_class:
                case 0:
                    match effect_type:
                        case "kAbsorbDamage":
                            if protected:
                                new_line += f"{param} {school}{emojis.PABSORB}"
                            else:
                                new_line += f"{param} {school}{emojis.ABSORB}"
                                
                        case "kAbsorbHeal":
                            if protected:
                                new_line += f"{param} {emojis.HEART}{emojis.PABSORB}"
                            else:
                                new_line += f"{param} {emojis.HEART}{emojis.ABSORB}"
                                
                        case "kAddCombatTriggerList":
                            new_line += f"Add to Combat Trigger List"
                        case "kAddSpellToDeck":
                            object_name = await self.fetch_object_name_from_id(param)
                            new_line += f"Add {object_name[0][3]} To Deck"
                        case "kAddSpellToHand":
                            object_name = await self.fetch_object_name_from_id(param)
                            new_line += f"Add {object_name[0][3]} To Hand"
                        case "kAutoPass":
                            new_line += f"Auto Pass"
                        case "kBacklashDamage":
                            new_line += f"{school} Backlash"
                        case "kCloakedCharm":
                            if protected:
                                new_line += f"{param}% {emojis.CLOAK}{school}{emojis.PCHARM}"
                            else:
                                new_line += f"{param}% {emojis.CLOAK}{school}{emojis.CHARM}"
                            
                        case "kCloakedWard":
                            if protected:
                                new_line += f"{param}% {emojis.CLOAK}{school}{emojis.PWARD}"
                            else:
                                new_line += f"{param}% {emojis.CLOAK}{school}{emojis.WARD}"
                            
                        case "kCloakedWardNoRemove":
                            if protected:
                                new_line += f"{param}% {emojis.CLOAK}{school}{emojis.PWARD} No Remove"
                            else:
                                new_line += f"{param}% {emojis.CLOAK}{school}{emojis.WARD} No Remove"
                            
                        case "kClue":
                            new_line += f"Spy {param}{emojis.ROUNDS}"
                        case "kCollectEssence":
                            new_line += f"Extract"
                        case "kConfusion":
                            new_line += f"{param}% Confuse"
                        case "kCritBlock":
                            new_line += f"{param}% {school}{emojis.BLOCK}"
                        case "kCritBoost" | "kCritBoostSchoolSpecific":
                            new_line += f"{param}% {school}{emojis.CRIT}"
                        case "kDamage":
                            new_line += f"{param} {school}{emojis.DAMAGE}"
                        case "kDamageNoCrit":
                            new_line += f"{param} {school}{emojis.DAMAGE} No Crit"
                        case "kDamageOverTime":
                            if protected:
                                new_line += f"{param} {school}{emojis.PDOT}"
                            else:
                                new_line += f"{param} {school}{emojis.DOT}"
                                
                        case "kDamagePerTotalPipPower":
                            new_line += f"{rounds} {school}{emojis.DAMAGE} per {emojis.ALL_ENEMIES}{emojis.PIP}"
                        case "kDampen":
                            new_line += f"Max {param} {emojis.PIP}"
                        case "kDeferredDamage":
                            if protected:
                                new_line += f"{param} {school}{emojis.PBOMB}"
                            else:
                                new_line += f"{param} {school}{emojis.BOMB}"
                                
                        case "kDetonateOverTime":
                            match disposition:
                                case 0:
                                    new_line += f"Detonate {int(heal_modifier*100)}% {param} {emojis.DOT}/{emojis.HOT}"
                                case 1:
                                    new_line += f"Activate {int(heal_modifier*100)}% {param} {emojis.HOT}"
                                case 2:
                                    new_line += f"Detonate {int(heal_modifier*100)}% {param} {emojis.DOT}"
                        
                        case "kDispel":
                            new_line += f"{emojis.DISPEL}{school}"
                        case "kDispelBlock":
                            new_line += f"{emojis.DISPEL} Block"
                        case "kDivideDamage":
                            new_line += f"Divide {param} {school}{emojis.DAMAGE}"
                        case "kExitCombat":
                            new_line += f"Exit Combat"
                        case "kForceTargetable":
                            new_line += f"Force Targetable"
                        case "kHeal" | "kHealByWard" | "kSetHealPercent":
                            new_line += f"{param} {school}{emojis.HEART}"
                        case "kHealOverTime":
                            new_line += f"{param} {school}{emojis.HOT}"
                        case "kHealPercent" | "kMaxHealthHeal":
                            new_line += f"{param}% {school}{emojis.HEART}"
                        case "kInstantKill":
                            new_line += f"{param} {school} Instant Kill"
                        case "kInvalidSpellEffect":
                            new_line += f"Invalid Spell Effect"
                        case "kKillCreature":
                            new_line += f"Kill {param}"
                        case "kMakeTargetable":
                            new_line += f"Make Targetable"
                        case "kMaxHealthDamage":
                            new_line += f"{param}% Max HP {school}{emojis.DAMAGE}"
                        case "kMaximumIncomingDamage":
                            new_line += f"{param} Equalize"
                        case "kMindControl":
                            new_line += f"Beguile {param}{emojis.ROUNDS}"
                        case "kModifyAccuracy" | "kModifyCardAccuracy":
                            new_line += f"{param}% {school}{emojis.ACCURACY}"
                        case "kModifyCardArmorPiercing" | "kModifyCardOutgoingArmorPiercing":
                            new_line += f"+{param}% {school}{emojis.PIERCE}"
                        case "kModifyCardCloak":
                            new_line += f"{emojis.CLOAK}"
                        case "kModifyCardDamage":
                            new_line += f"+{param} {emojis.DAMAGE}"
                        case "kModifyCardDamagebyRank":
                            new_line += f"+{param} per {emojis.PIP} (MAX: {rounds})"
                        case "kModifyCardHeal":
                            new_line += f"+{param} {emojis.HEART}"
                        case "kModifyCardIncomingDamage":
                            match disposition:
                                case 0 | 1:
                                    new_line += f"{param}% {emojis.WARD}"
                                case 2:
                                    new_line += f"+{param}% {emojis.TRAP}"
                        
                        case "kModifyCardMutation":
                            object_name = await self.fetch_object_name_from_id(param)
                            new_line += f"Mutate to {object_name}"
                        case "kModifyCardRank":
                            new_line += f"Modify Rank by {param} {emojis.PIP}"
                        case "kModifyHate":
                            if param > 0:
                                new_line += f"+{param} Hate"
                            elif param < 0:
                                new_line += f"{param} Hate"
                            else:
                                new_line += f"Devour"
                        
                        case "kModifyIncomingArmorPiercing":
                            if rounds == 0 and target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.PIERCE}{emojis.TRAP}"
                                else:
                                    new_line += f"{param}% {school}{emojis.PIERCE}{emojis.WARD}"
                            elif target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.PIERCE}{emojis.AURA_NEGATIVE}"
                                else:
                                    new_line += f"{param}% {school}{emojis.PIERCE}{emojis.AURA}"
                            else:
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.PIERCE}"
                                else:
                                    new_line += f"{param}% {school}{emojis.PIERCE}"
                        
                        case "kModifyIncomingDamage":
                            if rounds == 0 and target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.TRAP}"
                                else:
                                    new_line += f"{param}% {school}{emojis.SHIELD}"
                            elif target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.AURA_NEGATIVE}"
                                else:
                                    new_line += f"{param}% {school}{emojis.AURA}"
                            else:
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.DAMAGE}"
                                else:
                                    new_line += f"{param}% {school}{emojis.DAMAGE}"
                        
                        case "kModifyIncomingDamageFlat":
                            if rounds == 0 and target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param} {school}{emojis.TRAP}"
                                else:
                                    new_line += f"{param} {school}{emojis.SHIELD}"
                            elif target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param} {school}{emojis.AURA_NEGATIVE}"
                                else:
                                    new_line += f"{param} {school}{emojis.AURA}"
                            else:
                                if param >= 0:
                                    new_line += f"+{param} {school}{emojis.FLAT_DAMAGE}"
                                else:
                                    new_line += f"{param} {school}{emojis.FLAT_DAMAGE}"
                        
                        case "kModifyIncomingDamageOverTime":
                            if rounds == 0 and target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.DOT}{emojis.JINX}"
                                else:
                                    new_line += f"{param}% {school}{emojis.DOT}{emojis.WARD}"
                            elif target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.DOT}{emojis.AURA_NEGATIVE}"
                                else:
                                    new_line += f"{param}% {school}{emojis.DOT}{emojis.AURA}"
                            else:
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.DOT}{emojis.DAMAGE}"
                                else:
                                    new_line += f"{param}% {school}{emojis.DOT}{emojis.DAMAGE}"
                        
                        case "kModifyIncomingDamageType":
                            new_line += f"Convert {school} to {database.school_prism_values[param]} {emojis.JINX}"
                        case "kModifyIncomingHeal":
                            if rounds == 0 and target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.HEART}{emojis.JINX}"
                                else:
                                    new_line += f"{param}% {school}{emojis.HEART}{emojis.JINX}"
                            elif target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.HEART}{emojis.AURA}"
                                else:
                                    new_line += f"{param}% {school}{emojis.HEART}{emojis.AURA_NEGATIVE}"
                            else:
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.HEART}"
                                else:
                                    new_line += f"{param}% {school}{emojis.HEART}"
                        
                        case "kModifyIncomingHealFlat":
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
                        
                        case "kModifyIncomingHealOverTime":
                            if rounds == 0 and target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.HOT}{emojis.JINX}"
                                else:
                                    new_line += f"{param}% {school}{emojis.HOT}{emojis.JINX}"
                            elif target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.HOT}{emojis.AURA}"
                                else:
                                    new_line += f"{param}% {school}{emojis.HOT}{emojis.AURA_NEGATIVE}"
                            else:
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.HOT}"
                                else:
                                    new_line += f"{param}% {school}{emojis.HOT}"
                        
                        case "kModifyOutgoingArmorPiercing":
                            if rounds == 0 and target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.PIERCE}{emojis.CHARM}"
                                else:
                                    new_line += f"{param}% {school}{emojis.PIERCE}{emojis.CURSE}"
                            elif target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.PIERCE}{emojis.AURA}"
                                else:
                                    new_line += f"{param}% {school}{emojis.PIERCE}{emojis.AURA_NEGATIVE}"
                            else:
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.PIERCE}"
                                else:
                                    new_line += f"{param}% {school}{emojis.PIERCE}"
                        
                        case "kModifyOutgoingDamage":
                            if rounds == 0 and target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.BLADE}"
                                else:
                                    new_line += f"{param}% {school}{emojis.WEAKNESS}"
                            elif target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.DAMAGE}{emojis.AURA}"
                                else:
                                    new_line += f"{param}% {school}{emojis.DAMAGE}{emojis.AURA_NEGATIVE}"
                            else:
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.DAMAGE}"
                                else:
                                    new_line += f"{param}% {school}{emojis.DAMAGE}"
                        
                        case "kModifyOutgoingDamageFlat":
                            if rounds == 0 and target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param} {school}{emojis.BLADE}"
                                else:
                                    new_line += f"{param} {school}{emojis.WEAKNESS}"
                            elif target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param} {school}{emojis.DAMAGE}{emojis.AURA}"
                                else:
                                    new_line += f"{param} {school}{emojis.DAMAGE}{emojis.AURA_NEGATIVE}"
                            else:
                                if param >= 0:
                                    new_line += f"+{param} {school}{emojis.FLAT_DAMAGE}"
                                else:
                                    new_line += f"{param} {school}{emojis.FLAT_DAMAGE}"
                        
                        case "kModifyOutgoingDamageType":
                            new_line += f"Convert {school} to {database.school_prism_values[param]} {emojis.CHARM}"
                        case "kModifyOutgoingHeal":
                            if rounds == 0 and target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.HEART}{emojis.CHARM}"
                                else:
                                    new_line += f"{param}% {school}{emojis.HEART}{emojis.CURSE}"
                            elif target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.HEART}{emojis.AURA}"
                                else:
                                    new_line += f"{param}% {school}{emojis.HEART}{emojis.AURA_NEGATIVE}"
                            else:
                                if param >= 0:
                                    new_line += f"+{param}% {school}{emojis.HEART}"
                                else:
                                    new_line += f"{param}% {school}{emojis.HEART}"
                                    
                        case "kModifyOutgoingHealFlat":
                            if rounds == 0 and target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param} {school}{emojis.HEART}{emojis.CHARM}"
                                else:
                                    new_line += f"{param} {school}{emojis.HEART}{emojis.CURSE}"
                            elif target != "kGlobal":
                                if param >= 0:
                                    new_line += f"+{param} {school}{emojis.HEART}{emojis.AURA}"
                                else:
                                    new_line += f"{param} {school}{emojis.HEART}{emojis.AURA_NEGATIVE}"
                            else:
                                if param >= 0:
                                    new_line += f"+{param} {school}{emojis.HEART}"
                                else:
                                    new_line += f"{param} {school}{emojis.HEART}"
                        
                        case "kModifyOverTimeDuration":
                            match disposition:
                                case 0 | 1:
                                    new_line += f"Add {emojis.HOT}"
                                case 2:
                                    new_line += f"Add {emojis.DOT}"
                        
                        case "kModifyPipRoundRate":
                            if param >= 0:
                                new_line += f"+{param} {emojis.PIP} Gain Per Round"
                            else:
                                new_line += f"{param} {emojis.PIP} Gain Per Round"
                        
                        case "kModifyPips":
                            if param >= 0:
                                new_line += f"+{param} {emojis.PIP}"
                            else:
                                new_line += f"{param} {emojis.PIP}"
                        
                        case "kModifyPowerPipChance":
                            if param >= 0:
                                new_line += f"+{param}% {emojis.POWER_PIP} Chance"
                            else:
                                new_line += f"{param}% {emojis.POWER_PIP} Chance"
                        
                        case "kModifyPowerPips":
                            if param >= 0:
                                new_line += f"+{param} {emojis.POWER_PIP}"
                            else:
                                new_line += f"{param} {emojis.POWER_PIP}"
                        
                        case "kModifyRank":
                            if param >= 0:
                                new_line += f"+{param} {school} Rank"
                            else:
                                new_line += f"{param} {school} Rank"
                        
                        case "kModifySchoolPips":
                            if param >= 0:
                                new_line += f"+{param} {school}{emojis.POWER_PIP}"
                            else:
                                new_line += f"{param} {school}{emojis.POWER_PIP}"
                        
                        case "kModifyShadowCreatureLevel":
                            if param >= 0:
                                new_line += f"+{param} Shadow Creature Level"
                            else:
                                new_line += f"{param} Shadow Creature Level"
                        
                        case "kModifyShadowPips":
                            if param >= 0:
                                new_line += f"+{param} {emojis.SHADOW_PIP}"
                            else:
                                new_line += f"{param} {emojis.SHADOW_PIP}"
                        
                        case "kPacify":
                            new_line += f"Pacify"
                        case "kPipConversion":
                            if param >= 0:
                                new_line += f"+{param} {emojis.PIP} from Incoming Rank {pip_num} Spells"
                            else:
                                new_line += f"{param} {emojis.PIP} from Incoming Rank {pip_num} Spells"
                        case "kPolymorph":
                            new_line += f"Polymorph into {param}"
                        case "kPowerPipConversion":
                            if param >= 0:
                                new_line += f"+{param} {emojis.POWER_PIP} from Incoming Rank {pip_num} Spells"
                            else:
                                new_line += f"{param} {emojis.POWER_PIP} from Incoming Rank {pip_num} Spells"
                        case "kProtectCardBeneficial":
                            new_line += f"Protect {emojis.CHARM}"
                        case "kProtectCardHarmful":
                            new_line += f"Protect {emojis.JINX}"
                        case "kPushCharm":
                            new_line += f"Push {param} {emojis.CURSE}"
                        case "kPushOverTime":
                            new_line += f"Push {param} {emojis.DOT}"
                        case "kPushWard":
                            new_line += f"Push {param} {emojis.JINX}"
                        case "kReduceOverTime":
                            new_line += f"{param} {emojis.DOT}{emojis.ROUNDS}"
                        case "kRemoveAura":
                            new_line += f"Remove {emojis.AURA}"
                        case "kRemoveCharm":
                            match disposition:
                                case 0 | 1:
                                    new_line += f"Remove {param} {emojis.CHARM}"
                                case 2:
                                    new_line += f"Remove {param} {emojis.CURSE}"
                        case "kRemoveCombatTriggerList":
                            new_line += "Remove Combat Trigger List"
                        case "kRemoveOverTime":
                            match disposition:
                                case 0 | 1:
                                    new_line += f"Remove {param} {emojis.HOT}"
                                case 2:
                                    new_line += f"Remove {param} {emojis.DOT}"
                        case "kRemoveStunBlock":
                            new_line += f"Remove {emojis.STUN_BLOCK}"
                        case "kRemoveWard":
                            match disposition:
                                case 0 | 1:
                                    new_line += f"Remove {param} {emojis.WARD}"
                                case 2:
                                    new_line += f"Remove {param} {emojis.JINX}"
                        case "kReshuffle":
                            new_line += "Reshuffle"
                        case "kResumePips":
                            new_line += "Resume Pips"
                        case "kSelectShadowCreatureAttackTarget":
                            new_line += "Select Shadow Creature Attack Target"
                        case "kShadowDecrementTurn":
                            new_line += "Shadow Decrement Turn"
                        case "kSpawnCreature" | "kSummonCreature":
                            new_line += f"Summon {param}"
                        case "kStealCharm":
                            match disposition:
                                case 0 | 1:
                                    new_line += f"Steal {param} {emojis.CHARM}"
                                case 2:
                                    new_line += f"Push {param} {emojis.CURSE}"
                        case "kStealHealth":
                            new_line += f"{param} {school}{emojis.STEAL} ({heal_modifier*100}%)"
                        case "kStealOverTime":
                            match disposition:
                                case 0 | 1:
                                    new_line += f"Steal {param} {emojis.HOT}"
                                case 2:
                                    new_line += f"Push {param} {emojis.DOT}"
                        case "kStealWard":
                            match disposition:
                                case 0 | 1:
                                    new_line += f"Steal {param} {emojis.WARD}"
                                case 2:
                                    new_line += f"Push {param} {emojis.JINX}"
                        case "kStopAutoPass":
                            new_line += "Stop Auto Pass"
                        case "kStopVanish":
                            new_line += "Stop Vanish"
                        case "kStun":
                            new_line += f"{emojis.STUN} {param}{emojis.ROUNDS}"
                        case "kStunBlock":
                            new_line += f"{param} {emojis.STUN_BLOCK}"
                        case "kSuspendPips":
                            new_line += "Suspend Pips"
                        case "kSwapAll":
                            new_line += "Swap All"
                        case "kSwapCharm":
                            match disposition:
                                case 0:
                                    new_line += f"Swap {emojis.CHARM}/{emojis.CURSE}"
                                case 1:
                                    new_line += f"Swap {emojis.CHARM}"
                                case 2:
                                    new_line += f"Swap {emojis.CURSE}"
                        case "kSwapOverTime":
                            match disposition:
                                case 0:
                                    new_line += f"Swap {emojis.DOT}/{emojis.HOT}"
                                case 1:
                                    new_line += f"Swap {emojis.HOT}"
                                case 2:
                                    new_line += f"Swap {emojis.DOT}"
                        case "kSwapWard":
                            match disposition:
                                case 0:
                                    new_line += f"Swap {emojis.WARD}/{emojis.JINX}"
                                case 1:
                                    new_line += f"Swap {emojis.WARD}"
                                case 2:
                                    new_line += f"Swap {emojis.JINX}"
                        case "kTaunt":
                            new_line += f"Taunt"
                        case "kUnPolymorph":
                            new_line += f"Unpolymorph"
                        case "kUntargetable":
                            new_line += f"Untargetable"
                        case "kVanish":
                            new_line += f"Vanish"

                    if rounds > 0 and not effect_type in ["kDamage", "kClue", "kDamagePerTotalPipPower", "kDetonateOverTime", "kHealByWard", "kMindControl", "kModifyCardDamagebyRank", "kStun"]:
                        new_line += f" {rounds}{emojis.ROUNDS}"
                    
                    match target:
                        case "kEnemyTeamAllAtOnce" | "kEnemyTeam":
                            new_line += f" {emojis.ALL_ENEMIES_SQUARE}"
                        case "kSpell" | "kSpecificSpells":
                            new_line += f" {emojis.ENCHANTMENT}"
                        case "kSelf":
                            new_line += f" {emojis.SELF}"
                        case "kEnemySingle":
                            new_line += f" {emojis.ALL_ENEMIES}"
                        case "kFriendlyTeam" | "kFriendlyTeamAllAtOnce":
                            new_line += f" {emojis.ALL_FRIENDS_SQUARE}"
                        case "kFriendlySingle":
                            new_line += f" {emojis.ALL_FRIENDS}"
                        case "kGlobal":
                            new_line += f" {emojis.GLOBAL}"
                        case "kMinion":
                            new_line += f" {emojis.MINION}"
                        case "kMultiTargetEnemy":
                            new_line += f" {emojis.ALL_ENEMIES_SELECT}"
                        case "kMultiTargetFriendly":
                            new_line += f" {emojis.ALL_FRIENDS_SELECT}"
                    
                    if effect_type != "kInvalidSpellEffect":
                        effect_string.append(f"{new_line}\n")
                    await self.recursive_generate_effect_string(spell_effects, effect_string, nested_level+1, parent_is_x_pip=False, parent_id=effect_id)
                
                case 1:
                    effect_string.append("\n" + f"Random:\n")
                    await self.recursive_generate_effect_string(spell_effects, effect_string, nested_level+1, parent_is_x_pip=False, parent_id=effect_id)
                    effect_string.append("\n")
                
                case 2:
                    effect_string.append("\n" + f"Variable:\n")
                    await self.recursive_generate_effect_string(spell_effects, effect_string, nested_level+1, parent_is_x_pip=True, parent_id=effect_id)
                    effect_string.append("\n")
                
                case 3:
                    await self.recursive_generate_effect_string(spell_effects, effect_string, nested_level, parent_is_x_pip=False, parent_id=effect_id)
                
                case 4:
                    effect_string.append("\n" + f"{self.replace_condition_with_emojis(condition)}:\n")
                    await self.recursive_generate_effect_string(spell_effects, effect_string, nested_level+1, parent_is_x_pip=False, parent_id=effect_id)
                    effect_string.append("\n")
                
                case 5:
                    await self.recursive_generate_effect_string(spell_effects, effect_string, nested_level, parent_is_x_pip=False, parent_id=effect_id)


    async def generate_spell_effects_description(self, spell_effects):
        ret_list = []
        await self.recursive_generate_effect_string(spell_effects, ret_list)
        return "".join(ret_list)

    def parse_description(self, description, effects: List[tuple]) -> str:
        description = re.sub(r'#-?\d+:', '', description)
        description = re.sub("<[^>]*>", "", description)
        description = re.sub(r"\{[^{}]*\}", "", description)
        description = re.sub(r"%%", "%", description)
        #print(effects)
        #print(description)
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

                case "Gambit" | "Clear" | "Remove" | "Steal" | "Swap" | "Take" | "Echo" | "Detonate" | "or" | ":" | "/" | "if":
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
            parsed_description = self.replace_consecutive_duplicates(await self.generate_spell_effects_description(spell_effects))
            #self.condense_conditionals(parsed_description)
            print(len(parsed_description))
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
                discord_file = discord.File(f"PNG_Images\\{png_file}", filename=png_name)
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
        if type(interaction.channel) is PartialMessageable:
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
                closest_names = [(string, fuzz.token_set_ratio(name, string) + fuzz.ratio(name, string)) for string in self.bot.spell_list]
                closest_names = sorted(closest_names, key=lambda x: x[1], reverse=True)
                closest_names = list(zip(*closest_names))[0]
                
                for spell in closest_names:
                    rows = await self.fetch_spells_with_filter(spell, school, kind, rank, return_row=True)

                    if rows:
                        logger.info("Failed to find '{}' instead searching for {}", name, spell)
                        break

        if rows:
            embeds = [await self.build_spell_embed(row, show_spell_effects=show_spell_effects) for row in rows]
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
        if type(interaction.channel) is PartialMessageable:
            logger.info("{} searched for spells that contain '{}'", interaction.user.name, name)
        else:
            logger.info("{} searched for spells that contain '{}' in channel #{} of {}", interaction.user.name, name, interaction.channel.name, interaction.guild.name)

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
            embed = discord.Embed(description=f"Unable to find {name}.").set_author(name=f"Searching: {name}", icon_url=emojis.UNIVERSAL.url)

            await interaction.followup.send(embed=embed)

        
        



async def setup(bot: TheBot):
    await bot.add_cog(Spells(bot))
