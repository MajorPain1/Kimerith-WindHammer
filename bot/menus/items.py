from typing import List

import discord
from discord import ui


class ItemView(ui.View):
    def __init__(self, entries: List[discord.Embed], *, files: List[discord.File] = [], timeout: float | None = 180.0):
        super().__init__(timeout=timeout)

        self.entries = entries
        if files:
            self.files = list(files)
        else:
            self.files = []
        self.user = None
        self.current_page = 1
        self.total_entries = len(self.entries)

    def format_entry(self, entry: discord.Embed) -> discord.Embed:
        return entry.set_footer(
            text=f"Showing page {self.current_page}/{self.total_entries}"
        )

    def get_current_page(self) -> discord.Embed:
        # Make sure our page is always in bounds.
        self.current_page = min(self.current_page, self.total_entries)
        self.current_page = max(self.current_page, 1)

        # Return the formatted embed entry to display.
        entry = self.entries[self.current_page - 1]
        return self.format_entry(entry)
    
    def get_current_file(self) -> discord.Embed:
        if not self.files:
            return None
        
        # Make sure our page is always in bounds.
        self.current_page = min(self.current_page, self.total_entries)
        self.current_page = max(self.current_page, 1)

        # Return the formatted embed entry to display.
        file = self.files[self.current_page - 1]
        if file:
            file_name = file.filename.replace(" ", "")
            self.files[self.current_page - 1] = discord.File(f"PNG_Images\\{file_name}", filename=file.filename)
        else:
            self.files[self.current_page - 1] = None

        return file

    async def update(self, interaction: discord.Interaction):
        if self.files:
            file_list = []
            if self.get_current_file():
                file_list.append(self.get_current_file())

            await interaction.response.edit_message(
                embed=self.get_current_page(), view=self, attachments=file_list
            )
        else:
            await interaction.response.edit_message(
                embed=self.get_current_page(), view=self
            )

    @ui.button(style=discord.ButtonStyle.primary, emoji="⏪")
    async def goto_first_button(
        self, interaction: discord.Interaction, _button: ui.Button
    ):
        if interaction.user == self.user:
            self.current_page = 1
            await self.update(interaction)

    @ui.button(style=discord.ButtonStyle.primary, emoji="⬅️")
    async def back_button(self, interaction: discord.Interaction, _button: ui.Button):
        if interaction.user == self.user:
            self.current_page -= 1
            await self.update(interaction)

    @ui.button(style=discord.ButtonStyle.primary, emoji="➡️")
    async def forward_button(
        self, interaction: discord.Interaction, _button: ui.Button
    ):
        if interaction.user == self.user:
            self.current_page += 1
            await self.update(interaction)

    @ui.button(style=discord.ButtonStyle.primary, emoji="⏩")
    async def goto_last_button(
        self, interaction: discord.Interaction, _button: ui.Button
    ):
        if interaction.user == self.user:
            self.current_page = self.total_entries
            await self.update(interaction)

    async def start(self, interaction: discord.Interaction):
        self.user = interaction.user

        # When we only have one embed to show, we don't need to paginate.
        if self.total_entries == 1:
            if self.get_current_file():
                await interaction.followup.send(embed=self.entries[0], file=self.files[0])

            else:
                await interaction.followup.send(embed=self.entries[0])

        else:
            if self.get_current_file():
                await interaction.followup.send(embed=self.get_current_page(), view=self, file=self.get_current_file())
                await self.wait()

            else:
                await interaction.followup.send(embed=self.get_current_page(), view=self)
                await self.wait()
