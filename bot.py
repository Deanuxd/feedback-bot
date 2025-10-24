import os
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from openai import OpenAI
from datetime import datetime

from utils.logging_utils import log_message
from utils.cleanup import MessageCleanup
from config.database import db
from permissions import is_privileged, DEV_ROLES, MOD_ROLES

# Load environment variables from .env file
load_dotenv()

# Get the tokens securely
TOKEN = os.getenv("DISCORD_TOKEN")
OPEN_API_KEY = os.getenv("OPENAI_KEY")

TARGET_THREAD_ID = 1425907680479940688

def get_user_role(member: discord.Member) -> str:
    """Determine the highest priority role for a user."""
    if any(role.name in DEV_ROLES for role in member.roles):
        return "Dev"
    if any(role.name in MOD_ROLES for role in member.roles):
        return "Mod"
    return None

class FeedbackBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cleanup_manager = MessageCleanup()
    
    async def setup_hook(self):
        """Called when the bot is done preparing data"""
        print("Loading extensions...")
        await self.load_extension("commands.thread_commands")
        print("Extensions loaded!")
        # Start the cleanup task after bot is ready
        self.message_cleanup_task.start()
    
    @tasks.loop(hours=24)
    async def message_cleanup_task(self):
        """Run daily cleanup of old messages"""
        from datetime import timezone
        print(f"Running scheduled message cleanup at {datetime.now(timezone.utc)}")
        await self.cleanup_manager.cleanup_old_messages()
    
    @message_cleanup_task.before_loop
    async def before_cleanup(self):
        """Wait until the bot is ready before starting the task"""
        await self.wait_until_ready()

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True  # required to read messages
intents.guilds = True

# Remove default help command
bot = FeedbackBot(command_prefix="!", intents=intents, help_command=None)
client = OpenAI(api_key=OPEN_API_KEY)

# --- EVENTS ---
@bot.event
async def on_ready():
    """Called when the bot is ready."""
    print(f"Logged in as {bot.user.name}")
    print("Bot is ready!")

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
