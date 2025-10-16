import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from openai import OpenAI

from utils.logging_utils import log_message
from utils.db import db
from permissions import is_privileged, DEV_ROLES, MOD_ROLES

# Load environment variables from .env file
load_dotenv()

# Get the tokens securely
TOKEN = os.getenv("DISCORD_TOKEN")
OPEN_API_KEY = os.getenv("OPENAI_KEY")

TARGET_THREAD_ID = 1425907680479940688

BACKGROUND_PROMPT = """
You are an assistant that summarizes and analyzes user feedback from a Discord thread.
The messages are written by users/mods discussing features, issues, and ideas.
- Write concise, neutral summaries unless asked otherwise.
- Focus on grouping similar feedback together.
- Ignore jokes or unrelated chatter unless directly relevant.
- Maintain a professional tone suitable for a product team review.
- Take into account any replies to a message that contain important information regarding the original message, especially from Mods.
- Pay special attention to feedback from users with [Mod] or [Dev] roles, as they often provide important context or confirmations.

The following is the instruction given to users of the thread:
Thanks for taking the time to give feedback! Please provide specific details about what do want/need and context, especially regarding the UI, difficulty, gameplay, and quality of life improvements.

Yes:

UI: Make the UI scalable with a config in the configuration menu.
Difficulty: The enemies in the second level shouldn't be strong by default, maybe some scaling the first minute.
Gameplay: The cooldown for the "Katana" skill feels too long, disrupting the combat flow.
Quality of Life: Add a counter in the pause menu for in-game achievements.

No:

UI: The UI is bad.
Difficulty: The game is too hard.
Gameplay: Enemies are hitting are too fast.
Quality of Life: The game needs better quality of life.


NOTES
The following items are a Work in Progress and more info will be given about them in the future:

Translations
Multiplayer
Mod support
More maps
More characters and items
"""

def get_user_role(member: discord.Member) -> str:
    """Determine the highest priority role for a user."""
    if any(role.name in DEV_ROLES for role in member.roles):
        return "Dev"
    if any(role.name in MOD_ROLES for role in member.roles):
        return "Mod"
    return None

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True  # required to read messages
intents.guilds = True

# Remove default help command
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
client = OpenAI(api_key=OPEN_API_KEY)

# --- EVENTS ---
@bot.event
async def on_ready():
    """Called when the bot is ready."""
    print(f"Logged in as {bot.user.name}")
    print("Loading extensions...")
    await bot.load_extension("commands.thread_commands")
    print("Extensions loaded!")

@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Ignore command messages
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    # Only handle messages in the target thread
    if message.channel.id != TARGET_THREAD_ID:
        return

    # Skip non-text messages
    if not message.content.strip():
        return

    # Detect if message is a reply
    reply_to = None
    if message.reference and message.reference.resolved:
        reply_to = f"{message.reference.resolved.author} ({message.reference.resolved.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
    elif message.reference:
        try:
            ref = await message.channel.fetch_message(message.reference.message_id)
            reply_to = f"{ref.author} ({ref.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
        except Exception:
            pass

    # Get user's role if any
    role = get_user_role(message.author)

    # Save to database
    db.save_message(
        thread_id=message.channel.id,
        author=str(message.author),
        role=role,
        content=message.content.strip(),
        created_at=message.created_at,
        reply_to=reply_to,
    )

    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    """Handle message edits by logging an update line."""
    # Only track edits in the target thread
    if after.channel.id != TARGET_THREAD_ID:
        return

    # Skip if the content didn't actually change
    if before.content.strip() == after.content.strip():
        return

    # Skip non-text messages
    if not after.content.strip():
        return

    # Get user's role if any
    role = get_user_role(after.author)

    db.save_message(
        thread_id=after.channel.id,
        author=str(after.author),
        role=role,
        content=after.content.strip(),
        created_at=after.edited_at or after.created_at,
        edited=True,
    )

# --- RUN ---
bot.run(TOKEN)
