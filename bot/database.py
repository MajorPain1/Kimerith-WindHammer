from enum import IntFlag
from struct import unpack
from typing import Tuple, List
from dataclasses import dataclass

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
    PET_JEWEL = 1 << 0
    NO_AUCTION = 1 << 1
    CROWNS_ONLY = 1 << 2
    NO_GIFT = 1 << 3
    INSTANT_EFFECT = 1 << 4
    NO_COMBAT = 1 << 5
    NO_DROPS = 1 << 6
    NO_DYE = 1 << 7
    NO_HATCHMAKING = 1 << 8
    NO_PVP = 1 << 9
    NO_SELL = 1 << 10
    NO_SHATTER = 1 << 11
    NO_TRADE = 1 << 12
    PVP_ONLY = 1 << 13
    ARENA_POINTS_ONLY = 1 << 14
    BLUE_ARENA_POINTS_ONLY = 1 << 15


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


def translate_equip_school(school: int) -> str:
    school_emoji = _SCHOOLS[school & 0x7FFF_FFFF]
    if school & (1 << 31) != 0:
        return f"All schools except {school_emoji}"
    elif school == 0:
        return f"{school_emoji}"
    else:
        return f"{school_emoji} only"


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
    "Weakness_image": WEAKNESS
}

def translate_type_emoji(icon_name: str) -> PartialEmoji:
    try:
        return _TYPE_EMOJIS[icon_name]
    except KeyError:
        return _TYPE_EMOJIS["Random_image"]

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
                        stats.append(StatObject(132, a, f" {PIP}"))
                    if b != 0:
                        stats.append(StatObject(133, b, f" {POWER_PIP}"))

                # Speed bonus
                case 5:
                    stats.append(StatObject(134, a, f"% {SPEED}"))

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
