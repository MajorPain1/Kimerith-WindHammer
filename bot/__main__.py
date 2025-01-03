import sys
from pathlib import Path

import discord
from discord.ext import commands
from loguru import logger

from . import TheBot

ROOT_DIR = Path(__file__).parent.parent

ITEMS_DB = ROOT_DIR / "items.db"

# Configure Discord gateway intents which should be used by the bot.
# See https://discordpy.readthedocs.io/en/stable/api.html#discord.Intents
INTENTS = discord.Intents.none()

INTENTS.emojis = True
INTENTS.guilds = True
INTENTS.guild_messages = True


def main():
    logger.remove()
    logger.enable("wizbot")
    logger.add(sys.stderr, level="INFO")
    logger.add(sys.stderr, level="ERROR", filter="discord")

    bot = TheBot(
        ITEMS_DB,
        command_prefix=commands.when_mentioned,
        case_insensitive=True,
        allowed_mentions=discord.AllowedMentions(
            everyone=False, roles=False, users=False
        ),
        max_messages=10_000,
        intents=INTENTS,
    )

    bot.run()


if __name__ == "__main__":
    main()
