from typing import Literal, Optional

import discord
from discord.ext import commands

from .. import TheBot


class Owner(commands.Cog, name="owner"):
    def __init__(self, bot: TheBot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context[TheBot]) -> bool:
        if not await self.bot.is_owner(ctx.author):
            await ctx.send("Sorry, this command may only be used by the bot owner")
            return False
        return True

    @commands.command()
    @commands.guild_only()
    async def sync(
        self,
        ctx: commands.Context[TheBot],
        guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None,
    ):
        if not guilds:
            match spec:
                case "~":
                    synced = await self.bot.tree.sync(guild=ctx.guild)
                case "*":
                    self.bot.tree.copy_global_to(guild=ctx.guild)
                    synced = await self.bot.tree.sync(guild=ctx.guild)
                case "^":
                    self.bot.tree.clear_commands(guild=ctx.guild)
                    await self.bot.tree.sync(guild=ctx.guild)
                    synced = []
                case _:
                    synced = await self.bot.tree.sync()

            desc = "globally" if spec is None else "to the current guild"
            print(synced)
            await ctx.send(f"Synced {len(synced)} commands {desc}!")

        else:
            synced = 0
            for guild in guilds:
                try:
                    await self.bot.tree.sync(guild=guild)
                except discord.HTTPException:
                    pass
                else:
                    synced += 1

            await ctx.send(
                f"Synced the command tree to {synced}/{len(guilds)} servers."
            )


async def setup(bot: TheBot):
    await bot.add_cog(Owner(bot))
