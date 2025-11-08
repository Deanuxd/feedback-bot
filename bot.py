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

# TARGET_THREAD_ID is no longer used since summaries are for any stored thread

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
        # Sync slash commands with Discord
        await self.tree.sync()
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
    # Removed TARGET_THREAD_ID check to allow multiple threads
    # if message.channel.id != TARGET_THREAD_ID:
    #     return

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
async def on_message_delete(message):
    """Handle message deletion by removing the message from the database."""
    # Skip bot's own messages
    if message.author == bot.user:
        return
        
    # Skip non-text messages
    if not message.content.strip():
        return
        
    # Delete the message from the database
    success = db.delete_message(
        thread_id=message.channel.id,
        author=str(message.author),
        created_at=message.created_at
    )
    
    if success:
        print(f"Deleted message from {message.author} in thread {message.channel.id}")

@bot.event
async def on_message_edit(before, after):
    """Handle message edits by updating the original message in the database."""
    # Only track edits in the target thread
    # Removed TARGET_THREAD_ID check to allow multiple threads
    # if after.channel.id != TARGET_THREAD_ID:
    #     return

    # Skip if the content didn't actually change
    if before.content.strip() == after.content.strip():
        return

    # Skip non-text messages
    if not after.content.strip():
        return

    # Get user's role if any
    role = get_user_role(after.author)

    # Update the existing message in the database instead of creating a new one
    # We need to find the message by matching author, original content, and timestamp
    # Since we don't store message IDs, we can match by author and created_at timestamp
    # This assumes no duplicate messages with same author and timestamp

    try:
        from models.database import Message
        with db.Session() as session:
            message = session.query(Message).filter(
                Message.thread_id == after.channel.id,
                Message.author == str(after.author),
                Message.created_at == before.created_at
            ).first()

            if message:
                message.content = after.content.strip()
                message.edited = True
                message.created_at = after.edited_at or after.created_at
                session.commit()
            else:
                # If message not found, fallback to saving as new message
                db.save_message(
                    thread_id=after.channel.id,
                    author=str(after.author),
                    role=role,
                    content=after.content.strip(),
                    created_at=after.edited_at or after.created_at,
                    edited=True,
                )
    except Exception as e:
        print(f"Error updating edited message: {e}")

# --- RUN ---
bot.run(TOKEN)
