import os
from datetime import datetime
from pathlib import Path

import aiosqlite
import discord
from discord.ext import commands
from loguru import logger

EXTENSIONS = Path(__file__).parent / "extensions"

FIND_ITEM_NAME_QUERY = """
SELECT locale_en.data FROM items
INNER JOIN locale_en ON locale_en.id == items.name
"""

FIND_SPELL_NAME_QUERY = """
SELECT locale_en.data FROM spells
INNER JOIN locale_en ON locale_en.id == spells.name
"""

FIND_MOB_NAME_QUERY = """
SELECT locale_en.data FROM mobs
INNER JOIN locale_en ON locale_en.id == mobs.name
"""

FIND_PET_NAME_QUERY = """
SELECT locale_en.data FROM pets
INNER JOIN locale_en ON locale_en.id == pets.name
"""

FIND_FISH_NAME_QUERY = """
SELECT locale_en.data FROM fish
INNER JOIN locale_en ON locale_en.id == fish.name
"""

class TheBot(commands.Bot):
    def __init__(self, db_path: Path, **kwargs):
        super().__init__(**kwargs)

        self.ready_once = False
        self.db_path = db_path
        self.db = None
        self.item_list = []
        self.spell_list = []
        self.mob_list = []
        self.pet_list = []
        self.fish_list = []
        self.uptime = datetime.now()

    async def on_ready(self):
        
        if self.ready_once:
            return
        self.ready_once = True
        
        # If we are not connected yet, connect to db.
        async with aiosqlite.connect(self.db_path) as db:
            self.db = await aiosqlite.connect(":memory:")
            await db.backup(self.db)

        # Make our item list        
        async with self.db.execute(FIND_ITEM_NAME_QUERY) as cursor:
            tuple_item_list = await cursor.fetchall()

        for i in tuple_item_list:
            self.item_list.append(i[0])

        # Make our spell list
        async with self.db.execute(FIND_SPELL_NAME_QUERY) as cursor:
            tuple_spell_list = await cursor.fetchall()

        for i in tuple_spell_list:
            self.spell_list.append(i[0])

        # Make our mob list
        async with self.db.execute(FIND_MOB_NAME_QUERY) as cursor:
            tuple_mob_list = await cursor.fetchall()

        for i in tuple_mob_list:
            self.mob_list.append(i[0])

        # Make our pet list
        async with self.db.execute(FIND_PET_NAME_QUERY) as cursor:
            tuple_pet_list = await cursor.fetchall()

        for i in tuple_pet_list:
            self.pet_list.append(i[0])

        # Make our fish list
        async with self.db.execute(FIND_FISH_NAME_QUERY) as cursor:
            tuple_fish_list = await cursor.fetchall()

        for i in tuple_fish_list:
            self.fish_list.append(i[0])

        # Load required bot extensions.
        #await self.load_extension("jishaku")
        ext_count = await self.load_extensions_from_dir(EXTENSIONS)

        #await self.tree.sync()
        # Log information about the user.
        logger.info(f"Logged in as {self.user}")
        logger.info(f"Running with {ext_count} extensions")

    async def load_extensions_from_dir(self, path: Path) -> int:
        if not path.is_dir():
            return 0

        before = len(self.extensions.keys())

        extension_names = []
        current_working_directory = Path(os.getcwd())

        for subpath in path.glob("**/[!_]*.py"):  # Ignore if starts with _
            subpath = subpath.relative_to(current_working_directory)

            parts = subpath.with_suffix("").parts
            if parts[0] == ".":
                parts = parts[1:]

            extension_names.append(".".join(parts))

        for ext in extension_names:
            try:
                await self.load_extension(ext)
            except (commands.errors.ExtensionError, commands.errors.ExtensionFailed):
                logger.exception("Failed loading " + ext)

        return len(self.extensions.keys()) - before

    async def on_message(self, message: discord.Message, /):
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        if ctx.command is not None:
            await self.invoke(ctx)

    async def close(self):
        await self.db.close()

    def run(self):
        super().run(os.environ["DISCORD_TOKEN"])
