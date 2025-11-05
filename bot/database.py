from enum import IntFlag, Enum
from struct import unpack
from typing import Tuple, List
from dataclasses import dataclass
import math

import discord

from .emojis import *

_SCHOOL_COLORS = [
    discord.Color.greyple(), # Universal
    discord.Color.greyple(), # Universal
    discord.Color.red(), # Fire
    discord.Color.blue(), # Ice
    discord.Color.purple(), # Storm
    discord.Color.gold(), # Myth
    discord.Color.green(), # Life
    discord.Color.darker_grey(), # Death
    discord.Color.from_str("#d2b48c"), # Balance
    discord.Color.from_str("#feff00"), # Star
    discord.Color.from_str("#ffb000"), # Sun
    discord.Color.from_str("#8bdbff"), # Moon
    discord.Color.from_str("#10a800"), # Gardening
    discord.Color.dark_purple(), # Shadow
    discord.Color.from_str("#ffbb00"), # Fishing
    discord.Color.from_str("#feff00"), # Cantrips
    discord.Color.from_str("#9999b1"), # Castlemagic
    discord.Color.from_str("#9999b1"), # Whirlyburly
]

_PET_LEVELS = ["Baby", "Teen", "Adult", "Ancient", "Epic", "Mega", "Ultra"]

school_prism_values = {
    72777: ICE,
    78483: SUN,
    2330892: LIFE,
    2343174: FIRE,
    2625203: STAR,
    2448141: MYTH,
    2504141: MOON,
    78318724: DEATH,
    83375795: STORM,
    1027491821: BALANCE,
    1429009101: SHADOW
}

_SCHOOLS = [
    UNIVERSAL,
    UNIVERSAL,
    FIRE,
    ICE,
    STORM,
    MYTH,
    LIFE,
    DEATH,
    BALANCE,
    STAR,
    SUN,
    MOON,
    GARDENING,
    SHADOW,
    FISHING,
    CANTRIPS,
    CASTLEMAGIC,
    WHIRLYBURLY,
]

_SPELL_TYPES = [
    NONE,
    HEART,
    DAMAGE,
    CHARM,
    WARD,
    AURA,
    GLOBAL,
    AOE,
    STEAL,
    MANIPULATION,
    ENCHANTMENT,
    POLYMORPH,
    CURSE,
    JINX,
    MUTATE,
    CLOAK,
    SHADOW,
    SHADOW,
    SHADOW,
    AURA_NEGATIVE,
]

_ITEMS = [
    HAT,
    ROBE,
    BOOTS,
    WAND,
    ATHAME,
    AMULET,
    RING,
    DECK,
    JEWEL,
    MOUNT,
]

_ITEMS_STR = [
    "Hat",
    "Robe",
    "Shoes",
    "Weapon",
    "Athame",
    "Amulet",
    "Ring",
    "Deck",
    "Jewel",
    "Mount",
]

_SCHOOLS_STR = [
    "Fire",
    "Ice",
    "Storm",
    "Myth",
    "Life",
    "Death",
    "Balance",
    "Star",
    "Sun",
    "Moon",
    "Gardening",
    "Shadow",
    "Fishing",
    "Cantrips",
    "Castlemagic",
    "WhirlyBurly",
]

_SPELL_TYPES_STR = [
    "Any",
    "Healing",
    "Damage",
    "Charm",
    "Ward",
    "Aura",
    "Global",
    "AOE",
    "Steal",
    "Manipulation",
    "Enchantment",
    "Polymorph",
    "Curse",
    "Jinx",
    "Mutate",
    "Cloak",
    "Shadow",
    "Shadow",
    "Shadow",
    "NegativeAura"
]


_MONSTROLOGY_EXTRACTS = [
    "Undead",
    "Gobbler",
    "Mander",
    "Spider",
    "Colossus",
    "Cyclops",
    "Golem",
    "Draconian",
    "Treant",
    "Imp",
    "Pig",
    "Elephant",
    "Wyrm",
    "Dino",
    "Bird",
    "Insect",
    "Polar Bear",
    "Alien",
]

GARDENING_TYPES = [
    GROWING,
    PEST,
    SOIL,
    G_UTILITY,
    PROTECTION,
]

FISHING_TYPES = [
    CATCHING,
    FS_UTILITY,
]

CANTRIP_TYPES = [
    INCANTATION,
    BENEFICIAL,
    SIGIL,
    TELEPORTATION,
    RITUAL,
]

class MonstrologyKind(IntFlag):
    UNDEAD = 1 << 0
    GOBBLER = 1 << 1
    MANDER = 1 << 2
    SPIDER = 1 << 3
    COLOSSUS = 1 << 4
    CYCLOPS = 1 << 5
    GOLEM = 1 << 6
    DRACONIAN = 1 << 7
    TREANT = 1 << 8
    IMP = 1 << 9
    PIG = 1 << 10
    ELEPHANT = 1 << 11
    WYRM = 1 << 12
    DINO = 1 << 13
    PARROT = 1 << 14
    INSECT = 1 << 15
    POLAR_BEAR = 1 << 16
    ALIEN = 1 << 17


class ItemKind(IntFlag):
    HAT = 1 << 0
    ROBE = 1 << 1
    SHOES = 1 << 2
    WEAPON = 1 << 3
    ATHAME = 1 << 4
    AMULET = 1 << 5
    RING = 1 << 6
    DECK = 1 << 7
    JEWEL = 1 << 8
    MOUNT = 1 << 9


class ExtraFlags(IntFlag):
    SQUARE_JEWEL = 1 << 0
    CIRCLE_JEWEL = 1 << 1
    PET_JEWEL = 1 << 2
    TRIANGLE_JEWEL = 1 << 3
    TEAR_JEWEL = 1 << 4
    PIN_SQUARE_SHIELD = 1 << 5
    PIN_SQUARE_SWORD = 1 << 6
    PIN_SQUARE_PIP = 1 << 7
    NO_AUCTION = 1 << 8
    CROWNS_ONLY = 1 << 9
    NO_GIFT = 1 << 10
    INSTANT_EFFECT = 1 << 11
    NO_COMBAT = 1 << 12
    NO_DROPS = 1 << 13
    NO_DYE = 1 << 14
    NO_HATCHMAKING = 1 << 15
    NO_PVP = 1 << 16
    NO_SELL = 1 << 17
    NO_SHATTER = 1 << 18
    NO_TRADE = 1 << 19
    PVP_ONLY = 1 << 20
    ARENA_POINTS_ONLY = 1 << 21
    BLUE_ARENA_POINTS_ONLY = 1 << 22


@dataclass
class StatObject:
    order: int
    value: int
    string: str

    def to_string(self) -> str:
        if self.string.startswith(("Allows", "Invul", "Gives", "Maycasts", "-")):
            return self.string
        elif self.value > 0:
            return f"+{self.value}{self.string}"
        else:
            return f"{self.value}{self.string}"


def translate_flags(flag: int) -> List[str]:
    emoji_flags = []
    
    if flag & ExtraFlags.SQUARE_JEWEL:
        emoji_flags.append(f"{SOCKET_SQUARE}")
        
    if flag & ExtraFlags.CIRCLE_JEWEL:
        emoji_flags.append(f"{SOCKET_CIRCLE}")
    
    if flag & ExtraFlags.PET_JEWEL:
        emoji_flags.append(f"{SOCKET_STAR}")
        
    if flag & ExtraFlags.TRIANGLE_JEWEL:
        emoji_flags.append(f"{SOCKET_TRIANGLE}")
    
    if flag & ExtraFlags.TEAR_JEWEL:
        emoji_flags.append(f"{SOCKET_TEAR}")
        
    if flag & ExtraFlags.PIN_SQUARE_SHIELD:
        emoji_flags.append(f"{PIN_SHIELD}")
    
    if flag & ExtraFlags.PIN_SQUARE_SWORD:
        emoji_flags.append(f"{PIN_SWORD}")
    
    if flag & ExtraFlags.PIN_SQUARE_PIP:
        emoji_flags.append(f"{PIN_POWER}")
    
    if flag & ExtraFlags.NO_AUCTION:
        emoji_flags.append(f"{NO_AUCTION}")
        
    if flag & ExtraFlags.CROWNS_ONLY:
        emoji_flags.append(f"{CROWNS_ONLY}")
        
    if flag & ExtraFlags.NO_COMBAT:
        emoji_flags.append(f"{NO_COMBAT}")
        
    if flag & ExtraFlags.NO_DROPS:
        emoji_flags.append(f"{NO_DROPS}")
        
    if flag & ExtraFlags.NO_DYE:
        emoji_flags.append(f"{NO_DYE}")
        
    if flag & ExtraFlags.NO_HATCHMAKING:
        emoji_flags.append(f"{NO_HATCHMAKING}")
        
    if flag & ExtraFlags.NO_PVP:
        emoji_flags.append(f"{NO_PVP}")
        
    if flag & ExtraFlags.NO_SELL:
        emoji_flags.append(f"{NO_SELL}")
        
    if flag & ExtraFlags.NO_SHATTER:
        emoji_flags.append(f"{NO_SHATTER}")
        
    if flag & ExtraFlags.NO_TRADE:
        emoji_flags.append(f"{NO_TRADE}")
        
    if flag & ExtraFlags.PVP_ONLY:
        emoji_flags.append(f"{PVP_ONLY}")
        
    if flag & ExtraFlags.ARENA_POINTS_ONLY:
        emoji_flags.append(f"{ARENA_POINTS_ONLY}")
        
    if flag & ExtraFlags.BLUE_ARENA_POINTS_ONLY:
        emoji_flags.append(f"{BLUE_ARENA_POINTS_ONLY}")

    return emoji_flags



def _fnv_1a(data: bytes) -> int:
    state = 0xCBF2_9CE4_8422_2325
    for b in data:
        state ^= b
        state *= 0x0000_0100_0000_01B3
        state &= 0xFFFF_FFFF_FFFF_FFFF
    return state >> 1


_STAT_DISPLAY_TABLE = {
    _fnv_1a(b"CanonicalFireDamage"): f" {FIRE}{DAMAGE}",
    _fnv_1a(b"CanonicalIceDamage"): f" {ICE}{DAMAGE}",
    _fnv_1a(b"CanonicalStormDamage"): f" {STORM}{DAMAGE}",
    _fnv_1a(b"CanonicalMythDamage"): f" {MYTH}{DAMAGE}",
    _fnv_1a(b"CanonicalDeathDamage"): f" {DEATH}{DAMAGE}",
    _fnv_1a(b"CanonicalShadowDamage"): f" {SHADOW}{DAMAGE}",
    _fnv_1a(b"CanonicalAllDamage"): f" {DAMAGE}",
    _fnv_1a(b"CanonicalAllFishingLuck"): f"% {FISHING_LUCK}",
    _fnv_1a(b"CanonicalStormAccuracy"): f"% {STORM}{ACCURACY}",
    _fnv_1a(b"CanonicalFireAccuracy"): f"% {FIRE}{ACCURACY}",
    _fnv_1a(b"CanonicalIceAccuracy"): f"% {ICE}{ACCURACY}",
    _fnv_1a(b"CanonicalLifeAccuracy"): f"% {LIFE}{ACCURACY}",
    _fnv_1a(b"CanonicalDeathAccuracy"): f"% {DEATH}{ACCURACY}",
    _fnv_1a(b"CanonicalBalanceAccuracy"): f"% {BALANCE}{ACCURACY}",
    _fnv_1a(b"CanonicalMythAccuracy"): f"% {MYTH}{ACCURACY}",
    _fnv_1a(b"CanonicalShadowAccuracy"): f"% {SHADOW}{ACCURACY}",
    _fnv_1a(b"CanonicalAllAccuracy"): f"% {ACCURACY}",
    _fnv_1a(b"CanonicalStormArmorPiercing"): f" {STORM}{PIERCE}",
    _fnv_1a(b"CanonicalFireArmorPiercing"): f" {FIRE}{PIERCE}",
    _fnv_1a(b"CanonicalIceArmorPiercing"): f" {ICE}{PIERCE}",
    _fnv_1a(b"CanonicalLifeArmorPiercing"): f" {LIFE}{PIERCE}",
    _fnv_1a(b"CanonicalDeathArmorPiercing"): f" {DEATH}{PIERCE}",
    _fnv_1a(b"CanonicalBalanceArmorPiercing"): f" {BALANCE}{PIERCE}",
    _fnv_1a(b"CanonicalMythArmorPiercing"): f" {MYTH}{PIERCE}",
    _fnv_1a(b"CanonicalShadowArmorPiercing"): f" {SHADOW}{PIERCE}",
    _fnv_1a(b"CanonicalAllArmorPiercing"): f" {PIERCE}",
    _fnv_1a(b"CanonicalLifeHealing"): f"% {OUTGOING}{HEART}",
    _fnv_1a(b"CanonicalPowerPip"): f"% {POWER_PIP} Chance",
    _fnv_1a(b"CanonicalMaxMana"): f" Max {MANA}",
    _fnv_1a(b"CanonicalMaxHealth"): f" Max {HEALTH}",
    _fnv_1a(b"CanonicalFireFlatDamage"): f" {FIRE}{FLAT_DAMAGE}",
    _fnv_1a(b"CanonicalIceFlatDamage"): f" {ICE}{FLAT_DAMAGE}",
    _fnv_1a(b"CanonicalStormFlatDamage"): f" {STORM}{FLAT_DAMAGE}",
    _fnv_1a(b"CanonicalMythFlatDamage"): f" {MYTH}{FLAT_DAMAGE}",
    _fnv_1a(b"CanonicalDeathFlatDamage"): f" {DEATH}{FLAT_DAMAGE}",
    _fnv_1a(b"CanonicalShadowFlatDamage"): f" {SHADOW}{FLAT_DAMAGE}",
    _fnv_1a(b"CanonicalAllFlatDamage"): f" {FLAT_DAMAGE}",
    _fnv_1a(b"CanonicalFireReduceDamage"): f" {FIRE}{RESIST}",
    _fnv_1a(b"CanonicalIceReduceDamage"): f" {ICE}{RESIST}",
    _fnv_1a(b"CanonicalStormReduceDamage"): f" {STORM}{RESIST}",
    _fnv_1a(b"CanonicalMythReduceDamage"): f" {MYTH}{RESIST}",
    _fnv_1a(b"CanonicalDeathReduceDamage"): f" {DEATH}{RESIST}",
    _fnv_1a(b"CanonicalShadowReduceDamage"): f" {SHADOW}{RESIST}",
    _fnv_1a(b"CanonicalAllReduceDamage"): f" {RESIST}",
    _fnv_1a(b"CanonicalIncHealing"): f"% {INCOMING}{HEART}",
    _fnv_1a(b"CanonicalIncomingAccuracy"): f"% {ACCURACY}",
    _fnv_1a(b"CanonicalLifeReduceDamage"): f" {LIFE}{RESIST}",
    _fnv_1a(b"CanonicalBalanceReduceDamage"): f" {BALANCE}{RESIST}",
    _fnv_1a(b"CanonicalLifeDamage"): f" {LIFE}{DAMAGE}",
    _fnv_1a(b"CanonicalLifeFlatDamage"): f" {LIFE}{FLAT_DAMAGE}",
    _fnv_1a(b"CanonicalBalanceDamage"): f" {BALANCE}{DAMAGE}",
    _fnv_1a(b"CanonicalBalanceFishingLuck"): f"% {BALANCE}{FISHING_LUCK}",
    _fnv_1a(b"CanonicalDeathFishingLuck"): f"% {DEATH}{FISHING_LUCK}",
    _fnv_1a(b"CanonicalFireFishingLuck"): f"% {FIRE}{FISHING_LUCK}",
    _fnv_1a(b"CanonicalIceFishingLuck"): f"% {ICE}{FISHING_LUCK}",
    _fnv_1a(b"CanonicalLifeFishingLuck"): f"% {LIFE}{FISHING_LUCK}",
    _fnv_1a(b"CanonicaMythFishingLuck"): f"% {MYTH}{FISHING_LUCK}",
    _fnv_1a(b"CanonicaShadowFishingLuck"): f"% {SHADOW}{FISHING_LUCK}",
    _fnv_1a(b"CanonicaStormFishingLuck"): f"% {STORM}{FISHING_LUCK}",
    _fnv_1a(b"CanonicalBalanceFlatDamage"): f" {BALANCE}{FLAT_DAMAGE}",
    _fnv_1a(b"CanonicalMaxManaPercentReduce"): f"-100% Max {MANA}",
    _fnv_1a(b"XPPercent"): "XP",
    _fnv_1a(b"GoldPercent"): ":coin:",
    _fnv_1a(b"CanonicalMaxEnergy"): f" Max {ENERGY}",
    _fnv_1a(b"CanonicalAllCriticalHit"): f" {CRIT} Rating",
    _fnv_1a(b"CanonicalAllBlock"): f" {BLOCK} Rating",
    _fnv_1a(b"CanonicalAllPowerPipRating"): f"% {POWER_PIP} Chance",
    _fnv_1a(b"CanonicalAllReduceDamageRating"): f" {RESIST}",
    _fnv_1a(b"CanonicalAllAccuracyRating"): f" {ACCURACY}",
    _fnv_1a(b"CanonicalStormCriticalHit"): f" {STORM}{CRIT} Rating",
    _fnv_1a(b"CanonicalMythCriticalHit"): f" {MYTH}{CRIT} Rating",
    _fnv_1a(b"CanonicalLifeCriticalHit"): f" {LIFE}{CRIT} Rating",
    _fnv_1a(b"CanonicalIceCriticalHit"): f" {ICE}{CRIT} Rating",
    _fnv_1a(b"CanonicalFireCriticalHit"): f" {FIRE}{CRIT} Rating",
    _fnv_1a(b"CanonicalDeathCriticalHit"): f" {DEATH}{CRIT} Rating",
    _fnv_1a(b"CanonicalBalanceCriticalHit"): f" {BALANCE}{CRIT} Rating",
    _fnv_1a(b"CanonicalShadowCriticalHit"): f" {SHADOW}{CRIT} Rating",
    _fnv_1a(b"CanonicalBalanceBlock"): f" {BALANCE}{BLOCK} Rating",
    _fnv_1a(b"CanonicalDeathBlock"): f" {DEATH}{BLOCK} Rating",
    _fnv_1a(b"CanonicalFireBlock"): f" {FIRE}{BLOCK} Rating",
    _fnv_1a(b"CanonicalIceBlock"): f" {ICE}{BLOCK} Rating",
    _fnv_1a(b"CanonicalLifeBlock"): f" {LIFE}{BLOCK} Rating",
    _fnv_1a(b"CanonicalMythBlock"): f" {MYTH}{BLOCK} Rating",
    _fnv_1a(b"CanonicalStormBlock"): f" {STORM}{BLOCK} Rating",
    _fnv_1a(b"CanonicalShadowBlock"): f" {SHADOW}{BLOCK} Rating",
    _fnv_1a(b"CanonicalBalanceAccuracyRating"): f"% {BALANCE}{ACCURACY}",
    _fnv_1a(b"CanonicalDeathAccuracyRating"): f"% {DEATH}{ACCURACY}",
    _fnv_1a(b"CanonicalFireAccuracyRating"): f"% {FIRE}{ACCURACY}",
    _fnv_1a(b"CanonicalIceAccuracyRating"): f"% {ICE}{ACCURACY}",
    _fnv_1a(b"CanonicalLifeAccuracyRating"): f"% {LIFE}{ACCURACY}",
    _fnv_1a(b"CanonicalMythAccuracyRating"): f"% {MYTH}{ACCURACY}",
    _fnv_1a(b"CanonicalStormAccuracyRating"): f"% {STORM}{ACCURACY}",
    _fnv_1a(b"CanonicalShadowAccuracyRating"): f"% {SHADOW}{ACCURACY}",
    _fnv_1a(b"CanonicalBalanceReduceDamageRating"): f" {BALANCE}{RESIST}",
    _fnv_1a(b"CanonicalDeathReduceDamageRating"): f" {DEATH}{RESIST}",
    _fnv_1a(b"CanonicalFireReduceDamageRating"): f" {FIRE}{RESIST}",
    _fnv_1a(b"CanonicalIceReduceDamageRating"): f" {ICE}{RESIST}",
    _fnv_1a(b"CanonicalLifeReduceDamageRating"): f" {LIFE}{RESIST}",
    _fnv_1a(b"CanonicalMythReduceDamageRating"): f" {MYTH}{RESIST}",
    _fnv_1a(b"CanonicalStormReduceDamageRating"): f" {STORM}{RESIST}",
    _fnv_1a(b"CanonicalShadowReduceDamageRating"): f" {SHADOW}{RESIST}",
    _fnv_1a(b"CanonicalBalanceMastery"): f"Allows {POWER_PIP} with {BALANCE} spells",
    _fnv_1a(b"CanonicalDeathMastery"): f"Allows {POWER_PIP} with {DEATH} spells",
    _fnv_1a(b"CanonicalFireMastery"): f"Allows {POWER_PIP} with {FIRE} spells",
    _fnv_1a(b"CanonicalIceMastery"): f"Allows {POWER_PIP} with {ICE} spells",
    _fnv_1a(b"CanonicalLifeMastery"): f"Allows {POWER_PIP} with {LIFE} spells",
    _fnv_1a(b"CanonicalMythMastery"): f"Allows {POWER_PIP} with {MYTH} spells",
    _fnv_1a(b"CanonicalStormMastery"): f"Allows {POWER_PIP} with {STORM} spells",
    _fnv_1a(b"CanonicalStunResistance"): f"% {STUN_BLOCK}",
    _fnv_1a(b"ReduceDamageInvunerable"): f"Invulnerable to {DAMAGE}",
    _fnv_1a(b"CanonicalShadowPip"): f" {SHADOW_PIP_STAT}",
    _fnv_1a(b"CanonicalAllFlatReduceDamage"): f" {FLAT_RESIST}",
    _fnv_1a(b"CanonicalLifeFlatReduceDamage"): f" {LIFE}{FLAT_RESIST}",
    _fnv_1a(b"CanonicalDeathFlatReduceDamage"): f" {DEATH}{FLAT_RESIST}",
    _fnv_1a(b"CanonicalMythFlatReduceDamage"): f" {MYTH}{FLAT_RESIST}",
    _fnv_1a(b"CanonicalStormFlatReduceDamage"): f" {STORM}{FLAT_RESIST}",
    _fnv_1a(b"CanonicalIceFlatReduceDamage"): f" {ICE}{FLAT_RESIST}",
    _fnv_1a(b"CanonicalFireFlatReduceDamage"): f" {FIRE}{FLAT_RESIST}",
    _fnv_1a(b"CanonicalBalanceFlatReduceDamage"): f" {BALANCE}{FLAT_RESIST}",
    _fnv_1a(b"CanonicalShadowFlatReduceDamage"): f" {SHADOW}{FLAT_RESIST}",
    _fnv_1a(b"CanonicalWispBonus"): f" {HEALTH_WISP}{MANA_WISP}",
    _fnv_1a(b"CanonicalAllPipConversion"): f" {PIP_CONVERSION} Rating",
    _fnv_1a(b"CanonicalFirePipConversion"): f" {FIRE}{PIP_CONVERSION} Rating",
    _fnv_1a(b"CanonicalIcePipConversion"): f" {ICE}{PIP_CONVERSION} Rating",
    _fnv_1a(b"CanonicalLifePipConversion"): f" {LIFE}{PIP_CONVERSION} Rating",
    _fnv_1a(b"CanonicalDeathPipConversion"): f" {DEATH}{PIP_CONVERSION} Rating",
    _fnv_1a(b"CanonicalMythPipConversion"): f" {MYTH}{PIP_CONVERSION} Rating",
    _fnv_1a(b"CanonicalBalancePipConversion"): f" {BALANCE}{PIP_CONVERSION} Rating",
    _fnv_1a(b"CanonicalStormPipConversion"): f" {STORM}{PIP_CONVERSION} Rating",
    _fnv_1a(b"CanonicalShadowPipConversion"): f" {SHADOW}{PIP_CONVERSION} Rating",
    _fnv_1a(b"CanonicalMoonReduceDamage"): f" {MOON}{RESIST}",
    _fnv_1a(b"CanonicalSunReduceDamage"): f" {SUN}{RESIST}",
    _fnv_1a(b"CanonicalStarReduceDamage"): f" {STAR}{RESIST}",
    _fnv_1a(b"CanonicalShadowPipRating"): f" {SHADOW_PIP_STAT} Rating",
    _fnv_1a(b"CanonicalAllArchmastery"): f" {ARCHMASTERY} Rating",
}


_STAT_ORDER_TABLE = [
    # All
    _fnv_1a(b"CanonicalMaxHealth"),
    _fnv_1a(b"CanonicalMaxMana"),
    _fnv_1a(b"CanonicalMaxEnergy"),
    _fnv_1a(b"CanonicalAllFishingLuck"),
    _fnv_1a(b"CanonicalWispBonus"),
    _fnv_1a(b"CanonicalPowerPip"),
    _fnv_1a(b"XPPercent"),
    _fnv_1a(b"GoldPercent"),
    _fnv_1a(b"CanonicalAllPowerPipRating"),
    _fnv_1a(b"CanonicalAllFlatDamage"),
    _fnv_1a(b"CanonicalAllBlock"),
    _fnv_1a(b"CanonicalAllReduceDamage"),
    _fnv_1a(b"CanonicalAllReduceDamageRating"),
    _fnv_1a(b"CanonicalAllAccuracy"),
    _fnv_1a(b"CanonicalAllAccuracyRating"),
    _fnv_1a(b"CanonicalIncomingAccuracy"),
    _fnv_1a(b"CanonicalAllArmorPiercing"),
    _fnv_1a(b"CanonicalAllCriticalHit"),
    _fnv_1a(b"CanonicalAllPipConversion"),
    _fnv_1a(b"CanonicalAllFlatReduceDamage"),
    _fnv_1a(b"CanonicalAllDamage"),
    # Balance
    _fnv_1a(b"CanonicalBalanceReduceDamage"),
    _fnv_1a(b"CanonicalBalanceReduceDamageRating"),
    _fnv_1a(b"CanonicalBalanceFlatReduceDamage"),
    _fnv_1a(b"CanonicalBalanceAccuracy"),
    _fnv_1a(b"CanonicalBalanceAccuracyRating"),
    _fnv_1a(b"CanonicalBalanceArmorPiercing"),
    _fnv_1a(b"CanonicalBalanceFlatDamage"),
    _fnv_1a(b"CanonicalBalanceBlock"),
    _fnv_1a(b"CanonicalBalanceCriticalHit"),
    _fnv_1a(b"CanonicalBalancePipConversion"),
    _fnv_1a(b"CanonicalBalanceDamage"),
    _fnv_1a(b"CanonicalBalanceFishingLuck"),
    # Death
    _fnv_1a(b"CanonicalDeathReduceDamage"),
    _fnv_1a(b"CanonicalDeathReduceDamageRating"),
    _fnv_1a(b"CanonicalDeathFlatReduceDamage"),
    _fnv_1a(b"CanonicalDeathAccuracy"),
    _fnv_1a(b"CanonicalDeathAccuracyRating"),
    _fnv_1a(b"CanonicalDeathArmorPiercing"),
    _fnv_1a(b"CanonicalDeathFlatDamage"),
    _fnv_1a(b"CanonicalDeathBlock"),
    _fnv_1a(b"CanonicalDeathCriticalHit"),
    _fnv_1a(b"CanonicalDeathPipConversion"),
    _fnv_1a(b"CanonicalDeathDamage"),
    _fnv_1a(b"CanonicalDeathFishingLuck"),
    # Fire
    _fnv_1a(b"CanonicalFireReduceDamage"),                                  #1 Resist
    _fnv_1a(b"CanonicalFireReduceDamageRating"),                            #2 Resist
    _fnv_1a(b"CanonicalFireFlatReduceDamage"),                              #3 Flat Resist
    _fnv_1a(b"CanonicalFireAccuracy"),                                      #4 Acc
    _fnv_1a(b"CanonicalFireAccuracyRating"),                                #5 Acc
    _fnv_1a(b"CanonicalFireArmorPiercing"),                                 #6 Pierce
    _fnv_1a(b"CanonicalFireFlatDamage"),                                    #7 Flat Dmg
    _fnv_1a(b"CanonicalFireBlock"),                                         #8 Block
    _fnv_1a(b"CanonicalFireCriticalHit"),                                   #9 Crit
    _fnv_1a(b"CanonicalFirePipConversion"),                                 #10 Pserve
    _fnv_1a(b"CanonicalFireDamage"),                                        #11 Dmg
    _fnv_1a(b"CanonicalFireFishingLuck"),                                   #12 Fishing luck
    # Ice
    _fnv_1a(b"CanonicalIceReduceDamage"),
    _fnv_1a(b"CanonicalIceReduceDamageRating"),
    _fnv_1a(b"CanonicalIceFlatReduceDamage"),
    _fnv_1a(b"CanonicalIceAccuracy"),
    _fnv_1a(b"CanonicalIceAccuracyRating"),
    _fnv_1a(b"CanonicalIceArmorPiercing"),
    _fnv_1a(b"CanonicalIceFlatDamage"),
    _fnv_1a(b"CanonicalIceBlock"),
    _fnv_1a(b"CanonicalIceCriticalHit"),
    _fnv_1a(b"CanonicalIcePipConversion"),
    _fnv_1a(b"CanonicalIceDamage"),
    _fnv_1a(b"CanonicalIceFishingLuck"),
    # Life
    _fnv_1a(b"CanonicalLifeReduceDamage"),
    _fnv_1a(b"CanonicalLifeReduceDamageRating"),
    _fnv_1a(b"CanonicalLifeFlatReduceDamage"),
    _fnv_1a(b"CanonicalLifeAccuracy"),
    _fnv_1a(b"CanonicalLifeAccuracyRating"),
    _fnv_1a(b"CanonicalLifeArmorPiercing"),
    _fnv_1a(b"CanonicalLifeFlatDamage"),
    _fnv_1a(b"CanonicalLifeBlock"),
    _fnv_1a(b"CanonicalLifeCriticalHit"),
    _fnv_1a(b"CanonicalLifePipConversion"),
    _fnv_1a(b"CanonicalLifeDamage"),
    _fnv_1a(b"CanonicalLifeFishingLuck"),
    # Myth
    _fnv_1a(b"CanonicalMythReduceDamage"),
    _fnv_1a(b"CanonicalMythReduceDamageRating"),
    _fnv_1a(b"CanonicalMythFlatReduceDamage"),
    _fnv_1a(b"CanonicalMythAccuracy"),
    _fnv_1a(b"CanonicalMythAccuracyRating"),
    _fnv_1a(b"CanonicalMythArmorPiercing"),
    _fnv_1a(b"CanonicalMythFlatDamage"),
    _fnv_1a(b"CanonicalMythBlock"),
    _fnv_1a(b"CanonicalMythCriticalHit"),
    _fnv_1a(b"CanonicalMythPipConversion"),
    _fnv_1a(b"CanonicalMythDamage"),
    _fnv_1a(b"CanonicaMythFishingLuck"),
    # Storm
    _fnv_1a(b"CanonicalStormReduceDamage"),
    _fnv_1a(b"CanonicalStormReduceDamageRating"),
    _fnv_1a(b"CanonicalStormFlatReduceDamage"),
    _fnv_1a(b"CanonicalStormAccuracy"),
    _fnv_1a(b"CanonicalStormAccuracyRating"),
    _fnv_1a(b"CanonicalStormArmorPiercing"),
    _fnv_1a(b"CanonicalStormFlatDamage"),
    _fnv_1a(b"CanonicalStormBlock"),
    _fnv_1a(b"CanonicalStormCriticalHit"),
    _fnv_1a(b"CanonicalStormPipConversion"),
    _fnv_1a(b"CanonicalStormDamage"),
    _fnv_1a(b"CanonicaStormFishingLuck"),
    # Shadow
    _fnv_1a(b"CanonicalShadowReduceDamage"),
    _fnv_1a(b"CanonicalShadowReduceDamageRating"),
    _fnv_1a(b"CanonicalShadowFlatReduceDamage"),
    _fnv_1a(b"CanonicalShadowAccuracy"),
    _fnv_1a(b"CanonicalShadowAccuracyRating"),
    _fnv_1a(b"CanonicalShadowArmorPiercing"),
    _fnv_1a(b"CanonicalShadowFlatDamage"),
    _fnv_1a(b"CanonicalShadowBlock"),
    _fnv_1a(b"CanonicalShadowCriticalHit"),
    _fnv_1a(b"CanonicalShadowPipConversion"),
    _fnv_1a(b"CanonicalShadowDamage"),
    _fnv_1a(b"CanonicaShadowFishingLuck"),
    _fnv_1a(b"CanonicalShadowPipRating"),
    _fnv_1a(b"CanonicalShadowPip"),
    # Inc and Out
    _fnv_1a(b"CanonicalIncHealing"),
    _fnv_1a(b"CanonicalLifeHealing"),
    # Masteries
    _fnv_1a(b"CanonicalBalanceMastery"),
    _fnv_1a(b"CanonicalDeathMastery"),
    _fnv_1a(b"CanonicalFireMastery"),
    _fnv_1a(b"CanonicalIceMastery"),
    _fnv_1a(b"CanonicalLifeMastery"),
    _fnv_1a(b"CanonicalMythMastery"),
    _fnv_1a(b"CanonicalStormMastery"),
    # Bottom stuff
    _fnv_1a(b"CanonicalMoonReduceDamage"),
    _fnv_1a(b"CanonicalSunReduceDamage"),
    _fnv_1a(b"CanonicalStarReduceDamage"),
    _fnv_1a(b"CanonicalStunResistance"),
    _fnv_1a(b"ReduceDamageInvunerable"),
    _fnv_1a(b"CanonicalAllArchmastery"),
    _fnv_1a(b"CanonicalMaxManaPercentReduce"),
]

def translate_stat(stat: int) -> Tuple[int, str, bool]:
    try:
        display_stat = _STAT_DISPLAY_TABLE[stat]
        order_number = _STAT_ORDER_TABLE.index(stat)
    except KeyError:
        display_stat = " Unknown Stat"
        order_number = 2000000
    
    return order_number, display_stat


def unpack_stat_value(value: int) -> float:
    raw = value.to_bytes(4, "little")
    return unpack("<f", raw)[0]

def unpack_int_list(value: int) -> List[int]:
    raw = value.to_bytes(88, "little")
    return unpack("<22i", raw)


def translate_rarity(rarity: int) -> str:
    match rarity:
        case -1:
            return "Unknown"
        case 0:
            return "Common"
        case 1:
            return "Uncommon"
        case 2:
            return "Rare"
        case 3:
            return "Ultra-rare"
        case 4:
            return "Epic"


def translate_school(school: int) -> discord.PartialEmoji:
    return _SCHOOLS[school]


def translate_equip_school(school: int, secondary=False) -> str:
    school_emoji = _SCHOOLS[school & 0x7FFF_FFFF]
    school_str = "School"
    if secondary:
        school_str = "Magic Weaving"
    
    if school & (1 << 31) != 0:
        return f"All{secondary*' magic weaving'} schools except {school_emoji}"
    elif school == 0 and not secondary:
        return f"{school_emoji}"
    else:
        return f"{school_emoji} {school_str} Only"


def make_school_color(school: int) -> discord.Color:
    return _SCHOOL_COLORS[school & 0x7FFF_FFFF]


def get_item_icon_url(item: ItemKind) -> str:
    bit_index = item.value.bit_length() - 1
    return _ITEMS[bit_index].url


def get_item_str(item: ItemKind) -> str:
    bit_index = item.value.bit_length() - 1
    return _ITEMS_STR[bit_index]


def get_monstrology_string(monstro: MonstrologyKind) -> List[str]:
    extracts = []
    value = monstro.value
    while value > 0:
        bit_index = value.bit_length() - 1
        extracts.append(_MONSTROLOGY_EXTRACTS[bit_index])
        value -= 1 << bit_index
        
    return list(reversed(extracts))


def format_sockets(jewels: int) -> str:
    sockets = []

    while jewels != 0:
        socket = jewels & 0xF

        match socket >> 1:
            case 0:
                emoji = "???"
                description = "???"
            case 1:
                emoji = SOCKET_TEAR
                description = "Tear"
            case 2:
                emoji = SOCKET_CIRCLE
                description = "Circle"
            case 3:
                emoji = SOCKET_SQUARE
                description = "Square"
            case 4:
                emoji = SOCKET_TRIANGLE
                description = "Triangle"
            case 5:
                emoji = PIN_POWER
                description = "Power"
            case 6:
                emoji = PIN_SHIELD
                description = "Shield"
            case 7:
                emoji = PIN_SWORD
                description = "Sword"

            case _:
                raise ValueError("Unknown emoji type")

        if socket & (1 << 0) != 0:
            emoji = SOCKET_LOCKED

        sockets.append(f"{emoji} ({description})")

        jewels >>= 4

    return "\n".join(sockets)


def translate_pet_level(level: int) -> str:
    return _PET_LEVELS[level - 1]


_TYPE_EMOJIS = {
    "Damage_image": DAMAGE,
    "Heal_image": HEART,
    "Accuracy_image": ACCURACY,
    "Afterlife_image": AFTERLIFE,
    "All_Enemies_Square_image": ALL_ENEMIES_SQUARE,
    "All_Friends_Square_image": ALL_FRIENDS_SQUARE,
    "Armor_Penetration_image": PIERCE,
    "BlockRating_image": BLOCK,
    "CriticalRating_image": CRIT,
    "Damage_or_drain_image": DAMAGE_OR_DRAIN,
    "Elemental_image": ELEMENTAL,
    "MoonSchoolIcon": MOON,
    "FireSchoolIcon": FIRE,
    "IceSchoolIcon": ICE,
    "StormSchoolIcon": STORM,
    "BalanceSchoolIcon": BALANCE,
    "LifeSchoolIcon": LIFE,
    "DeathSchoolIcon": DEATH,
    "MythSchoolIcon": MYTH,
    "ShadowSchoolIcon": SHADOW,
    "ElementalSchoolIcon": ELEMENTAL,
    "SpiritSchoolIcon": SPIRIT,
    "Incoming_image": INCOMING,
    "Outgoing_image": OUTGOING,
    "Self_image": SELF,
    "ShadowPips_image": SHADOW_PIP_STAT,
    "ShadowPips02_image": SHADOW_PIP_STAT,
    "All_Enemies_image": ALL_ENEMIES,
    "All_Enemies_Wide_image": ALL_ENEMIES_SQUARE,
    "All_Friends_image": ALL_FRIENDS,
    "All_Friends_Wide_image": ALL_FRIENDS_SQUARE,
    "Dispel_image": DISPEL,
    "Minion_image": MINION,
    "Rounds_image": ROUNDS,
    "Stun_image": STUN,
    "Threat_image": THREAT,
    "Absorb_image": ABSORB,
    "Aura_Pos_image": AURA,
    "Aura_Neg_image": AURA_NEGATIVE,
    "Blade_image": BLADE,
    "Curse_image": CURSE,
    "Damage_Flat_image": FLAT_DAMAGE,
    "OT_Damage_image": DOT,
    "DeferredDamage_image": BOMB,
    "pDeferredDamage_image": PBOMB,
    "Global_image": GLOBAL,
    "OT_Heal_image": HOT,
    "Jinx_image": JINX,
    "pAbsorb_image": PABSORB,
    "pBlade_image": PBLADE,
    "pCharm_image": PCHARM,
    "pCurse_image": PCURSE,
    "pOT_Damage_image": PDOT,
    "pOT_Heal_image": PHOT,
    "Pips_image": PIP,
    "pJinx_image": PJINX,
    "Polymorph_image": POLYMORPH,
    "PowerPips_image": POWER_PIP,
    "pTrap_image": PTRAP,
    "pWard_image": PWARD,
    "Random_image": RANDOM,
    "Resist_image": RESIST,
    "Resist_Flat_image": FLAT_RESIST,
    "Steal_image": STEAL,
    "StunResist_image": STUN_BLOCK,
    "Trap_image": TRAP,
    "Ward_image": WARD,
    "Charm_image": CHARM,
    "Block_image": BLOCK,
    "All_Enemies_Wide": ALL_ENEMIES_SQUARE,
    "All_Friends_Wide": ALL_FRIENDS_SQUARE,
    "All_Enemies_Select": ALL_ENEMIES_SELECT,
    "All_Friends_Select": ALL_FRIENDS_SELECT,
    "Chromatic_Caster_image": CHROMATIC_CASTER,
    "Chromatic_Target_image": CHROMATIC_TARGET,
    "Shield_image": SHIELD,
    "Weakness_image": WEAKNESS,
    "ShadowPact": SHADOW_SELF,
    "FirePips_image": FIRE_PIP,
    "IcePips_image": ICE_PIP,
    "StormPips_image": STORM_PIP,
    "MythPips_image": MYTH_PIP,
    "LifePips_image": LIFE_PIP,
    "DeathPips_image": DEATH_PIP,
    "BalancePips_image": BALANCE_PIP,
    "WeavingChromatic_Target_image": WEAVING_TARGET,
    "WeavingChromatic_Caster_image": WEAVING_CASTER
}

def translate_type_emoji(icon_name: str) -> PartialEmoji:
    try:
        return _TYPE_EMOJIS[icon_name]
    except KeyError:
        return icon_name

async def fetch_raw_item_stats(db, item: int) -> List[StatObject]:
    stats = []

    async with db.execute(
        "SELECT * FROM item_stats WHERE item == ?", (item,)
    ) as cursor:
        async for row in cursor:
            a = row[3]
            b = row[4]

            match row[2]:
                # Regular stat
                case 1:
                    order, stat = translate_stat(a)
                    stats.append(StatObject(order, b, stat))

                # Starting pips
                case 2:
                    if a != 0:
                        stats.append(StatObject(1320, a, f" {PIP}"))
                    if b != 0:
                        stats.append(StatObject(1330, b, f" {POWER_PIP}"))

                # Speed bonus
                case 5:
                    stats.append(StatObject(1340, a, f"% {SPEED}"))

    return stats

def getStatIndexFromList(statlist: List[StatObject], statorder: int) -> int:
    for i, stat in enumerate(statlist):
        if stat.order == statorder:
            return i

    return -1

async def sum_stats(db, existing_stats: List[StatObject], equipped_items: List[int]):
    existing_stats_dict = {stat.order: stat for stat in existing_stats}

    for item_id in equipped_items:
        for stat in await fetch_raw_item_stats(db, item_id):
            existing_stat = existing_stats_dict.get(stat.order)
            
            if existing_stat is not None:
                index = getStatIndexFromList(existing_stats, existing_stat.order)
                existing_stats[index].value = stat.value + existing_stat.value
            else:
                existing_stats.append(stat)
                existing_stats_dict[stat.order] = stat

class Buff:
    def __init__(self, value, is_pierce):
        self.value = value
        self.modifier = (float(value) / 100) + 1
        self.is_pierce = is_pierce
    
    def __repr__(self) -> str:
        return f"{self.value=} {self.modifier=} {self.is_pierce=}"

def translate_buffs(buffs: str):
    buffs = buffs.replace("%", "")
    if buffs == "": return []
    
    buff_list = buffs.split(" ")
    buffs_as_modifier = []
    for buff in buff_list:
        try:
            if buff[-1] == "P":
                pierce_buff = buff.removesuffix("P")
                buff_float = float(pierce_buff)
                buffs_as_modifier.append(Buff(buff_float, True))
            else:
                buff_float = float(buff)
                buffs_as_modifier.append(Buff(buff_float, False))
                
        except ValueError:
            pass
    
    return buffs_as_modifier

def crit_multiplier(crit, block, pvp=True):
    if crit == 0: return 1
    if block == 0: return 2
    if pvp: return 2 - ((5*block) / (crit + (5*block)))
    return 2 - ((3*block) / (crit + (3*block)))

def pve_damage_curve(damage: int):
    float_dmg = float(damage) / 100
    
    l = 2.47 # Limit
    k0 = 237 # Start of curve
    n0 = 0 # Basically depricated
    l100 = l * 100
    k0n0 = k0 + n0
    k = math.log(l100 / (l100 - k0)) / k0
    n = math.log(1 - (k0n0 / l100)) + (k * k0n0)
    
    if float_dmg > (k0n0 / 100):
        return 1 + (l - (l * math.exp((-100 * k * float_dmg) + n)))
    
    return 1 + float_dmg

def calc_damage(base, damage: int, pierce: int, critical: int, buffs: List[Buff], mob_block: int, pvp: bool):
    ret = int(base * (1+(float(damage) / 100)))
    
    if buffs != []:
        for buff in buffs:
            if buff.is_pierce:
                if pierce >= -buff.value:
                    pierce += buff.value
                    
                else:
                    new_buff_modifier = (pierce / 100) + buff.modifier
                    pierce = 0
                    ret = int(ret * new_buff_modifier)
                
            else:
                ret = int(ret * buff.modifier)
    
    return ret, int(ret * crit_multiplier(critical, mob_block, pvp))

class SpellEffects(Enum):
    invalid_spell_effect = 0
    damage = 1
    damage_no_crit = 2
    heal = 3
    heal_percent = 4
    set_heal_percent = 113
    steal_health = 5
    reduce_over_time = 6
    detonate_over_time = 7
    push_charm = 8
    steal_charm = 9
    push_ward = 10
    steal_ward = 11
    push_over_time = 12
    steal_over_time = 13
    remove_charm = 14
    remove_ward = 15
    remove_over_time = 16
    remove_aura = 17
    swap_all = 18
    swap_charm = 19
    swap_ward = 20
    swap_over_time = 21
    modify_incoming_damage = 22
    modify_incoming_damage_flat = 119
    maximum_incoming_damage = 23
    modify_incoming_heal = 24
    modify_incoming_heal_flat = 118
    modify_incoming_damage_type = 25
    modify_incoming_armor_piercing = 26
    modify_outgoing_damage = 27
    modify_outgoing_damage_flat = 121
    modify_outgoing_heal = 28
    modify_outgoing_heal_flat = 120
    modify_outgoing_damage_type = 29
    modify_outgoing_armor_piercing = 30
    modify_outgoing_steal_health = 31
    modify_incoming_steal_health = 32
    bounce_next = 33
    bounce_previous = 34
    bounce_back = 35
    bounce_all = 36
    absorb_damage = 37
    absorb_heal = 38
    modify_accuracy = 39
    dispel = 40
    confusion = 41
    cloaked_charm = 42
    cloaked_ward = 43
    stun_resist = 44
    clue = 111
    pip_conversion = 45
    crit_boost = 46
    crit_block = 47
    polymorph = 48
    delay_cast = 49
    modify_card_cloak = 50
    modify_card_damage = 51
    modify_card_accuracy = 53
    modify_card_mutation = 54
    modify_card_rank = 55
    modify_card_armor_piercing = 56
    summon_creature = 65
    teleport_player = 66
    stun = 67
    dampen = 68
    reshuffle = 69
    mind_control = 70
    modify_pips = 71
    modify_power_pips = 72
    modify_shadow_pips = 73
    modify_hate = 74
    damage_over_time = 75
    heal_over_time = 76
    modify_power_pip_chance = 77
    modify_rank = 78
    stun_block = 79
    reveal_cloak = 80
    instant_kill = 81
    after_life = 82
    deferred_damage = 83
    damage_per_total_pip_power = 84
    modify_card_heal = 52
    modify_card_charm = 57
    modify_card_ward = 58
    modify_card_outgoing_damage = 59
    modify_card_outgoing_accuracy = 60
    modify_card_outgoing_heal = 61
    modify_card_outgoing_armor_piercing = 62
    modify_card_incoming_damage = 63
    modify_card_absorb_damage = 64
    cloaked_ward_no_remove = 86
    add_combat_trigger_list = 87
    remove_combat_trigger_list = 88
    backlash_damage = 89
    modify_backlash = 90
    intercept = 91
    shadow_self = 92
    shadow_creature = 93
    modify_shadow_creature_level = 94
    select_shadow_creature_attack_target = 95
    shadow_decrement_turn = 96
    crit_boost_school_specific = 97
    spawn_creature = 98
    un_polymorph = 99
    power_pip_conversion = 100
    protect_card_beneficial = 101
    protect_card_harmful = 102
    protect_beneficial = 103
    protect_harmful = 104
    divide_damage = 105
    collect_essence = 106
    kill_creature = 107
    dispel_block = 108
    confusion_block = 109
    modify_pip_round_rate = 110
    max_health_damage = 112
    untargetable = 114
    make_targetable = 115
    force_targetable = 116
    remove_stun_block = 117
    exit_combat = 122
    suspend_pips = 123
    resume_pips = 124
    auto_pass = 125
    stop_auto_pass = 126
    vanish = 127
    stop_vanish = 128
    max_health_heal = 129
    heal_by_ward = 130
    taunt = 131
    pacify = 132
    remove_target_restriction = 133
    convert_hanging_effect = 134
    add_spell_to_deck = 135
    add_spell_to_hand = 136
    modify_incoming_damage_over_time = 137
    modify_incoming_heal_over_time = 138
    modify_card_damage_by_rank = 139
    push_converted_charm = 140
    steal_converted_charm = 141
    push_converted_ward = 142
    steal_converted_ward = 143
    push_converted_over_time = 144
    steal_converted_over_time = 145
    remove_converted_charm = 146
    remove_converted_ward = 147
    remove_converted_over_time = 148
    modify_over_time_duration = 149
    modify_school_pips = 150
    shadow_pact = 151


class EffectTarget(Enum):
    invalid_target = 0
    spell = 1
    specific_spells = 2
    target_global = 3
    enemy_team = 4
    enemy_team_all_at_once = 5
    friendly_team = 6
    friendly_team_all_at_once = 7
    enemy_single = 8
    friendly_single = 9
    minion = 10
    friendly_minion = 17
    self = 11
    at_least_one_enemy = 13
    preselected_enemy_single = 12
    multi_target_enemy = 14
    multi_target_friendly = 15
    friendly_single_not_me = 16

def _make_placeholders(count: int) -> str:
    return ", ".join(["?"] * count)

def sql_chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]