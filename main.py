import settings
import discord
from discord import app_commands
from discord.ext import commands
import glob
from cogs.messagestats import is_owner

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=',,', intents=intents, owner_id=461496649324167168)


    
@bot.event
async def on_ready():
    print(f"Successfully logged in as User: {bot.user} (ID: {bot.user.id})")
    
    try:
        ext_filenames = glob.glob("cogs/**/*.py", recursive=True)
        extension_names = [filename.removesuffix(".py").replace("/", ".").replace("\\", ".") for filename in ext_filenames]
        for extension in extension_names:
            try:
                await bot.load_extension(extension)
                print(f"Loaded {extension}")
            except Exception as e:
                print(f"Failed to load extension {extension}: {e}")
    except Exception as e:
        print(f"Error during startup: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing commands {e}")

        
@bot.tree.command(name="hello")
@is_owner()
async def ping(interaction: discord.Integration):
    """ Answers with Pong! """
    await interaction.response.send_message("Pong!")

@bot.tree.command()
@is_owner()
async def load(interaction: discord.Interaction, cog_name:str):
    await bot.load_extension(f"cogs.{cog_name.lower()}")
    interaction.response.send_message(f"Successfully loaded {cog_name}")


@bot.tree.command()
@is_owner()
async def reload(interaction: discord.Interaction, cog_name: str = "all"):
    if(cog_name == "all"):
        for file in settings.COGS_DIR.glob("*.py"):
            if file.name.endswith(".py") and file.name != "__init__.py":
                print(f"cogs.{file.name[:-3]}")
                await bot.reload_extension(f"cogs.{file.name[:-3]}")
                await interaction.response.send_message("Reloaded all cogs.")
    else:
        await bot.reload_extension(f"cogs.{cog_name.lower()}")
        await interaction.response.send_message(f"Successfully loaded {cog_name}")       


@bot.tree.command()
@is_owner()
async def unload(interaction: discord.Interaction, cog_name:str):
    await bot.reload_extension(f"cogs.{cog_name.lower()}")
    await interaction.response.send_message(f"Reloaded {cog_name}")






bot.run(settings.DISCORD_SECRET)

