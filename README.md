# Kimerith-WindHammer
Repo for the W101 Discord Bot, Kimerith WindHammer

# Usage

Head over to the [kobold repository](https://github.com/vbe0201/kobold) and follow installation instructions in the README. Also do the optional steps to install Python library bindings.

Then, head over to the [wiztype repository](https://github.com/wizspoil/wiztype) and follow README instructions to dump a types JSON from the game client.

If you want images for the bot, create a SummonedImages folder, unpack Root.wad and \_Shared-WorldData.wad and put all .dds images from GUI\NpcPortraits and GUI\SummonedImages into the new SummonedImages folder
After all images are in, run `py DDS_To_PNG.py` to convert it all to PNG_Images

To create the database the bot uses go to https://github.com/MajorPain1/wizdb and follow the instructions. Copy items.db over when it is completed

Finally, edit the .env file to have the token of your discord bot

Run `pipenv run bot` to run the bot
