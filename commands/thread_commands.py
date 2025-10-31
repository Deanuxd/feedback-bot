import discord
from discord.ext import commands
from permissions import can_manage_threads, is_privileged
from utils.thread_store import save_thread, get_thread_by_name
from utils.logging_utils import log_message
from utils.migrate import migrate_log_to_db
from utils.time_utils import parse_timeframe, format_timeframe
from sqlalchemy.exc import SQLAlchemyError
from config.prompts import DEFAULT_PROMPT
from config.database import db, Thread, Message
from services.summarizer import SummarizerService
import os

# Initialize summarizer service
summarizer = SummarizerService()

async def summarize_thread(thread_info, timeframe=None):
    """Generate a summary for the specified thread using configured AI provider."""
    try:
        # Parse timeframe and get date range
        start_date, end_date = parse_timeframe(timeframe)
        
        # Get messages for the thread within the timeframe
        messages = db.get_messages(
            thread_info.thread_id,
            start_date=start_date,
            end_date=end_date
        )

        if not messages:
            return f"No messages found in this thread for {format_timeframe(start_date, end_date)}."

        # Format messages for the AI
        formatted_messages = []
        for msg in messages:
            role_prefix = f"[{msg.role}] " if msg.role else ""
            formatted_messages.append(f"{role_prefix}{msg.author}: {msg.content}")

        # Generate summary using configured AI provider
        return await summarizer.generate_summary(formatted_messages, DEFAULT_PROMPT)

    except Exception as e:
        print(f"Error generating summary: {e}")
        return f"Error generating summary: {str(e)}"

async def import_thread_history(thread: discord.Thread, progress_message = None):
    """Import all messages from a thread's history."""
    from datetime import datetime, timedelta
    retention_days = 30
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    messages_imported = 0
    
    try:
        async for msg in thread.history(limit=None, oldest_first=True):
            if not msg.author.bot and msg.content.strip():
                if msg.created_at < cutoff_date:
                    continue  # Skip messages older than retention period
                
                reply_to = None
                if msg.reference and msg.reference.resolved:
                    reply_to = f"{msg.reference.resolved.author} ({msg.reference.resolved.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
                elif msg.reference:
                    try:
                        ref = await msg.channel.fetch_message(msg.reference.message_id)
                        reply_to = f"{ref.author} ({ref.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
                    except Exception:
                        pass
                
                success = db.save_message(
                    thread_id=thread.id,
                    author=str(msg.author),
                    content=msg.content.strip(),
                    created_at=msg.created_at,
                    reply_to=reply_to
                )
                
                if success:
                    messages_imported += 1
                    
                    if progress_message and messages_imported % 100 == 0:
                        await progress_message.edit(content=f"📥 Importing messages... ({messages_imported} processed)")
        
        return messages_imported
        
    except SQLAlchemyError as e:
        print(f"Database error during import: {e}")
        raise Exception("Database error during message import")

class ThreadCommands(commands.Cog, name="Thread Commands"):
    """Commands for managing feedback threads"""
    
    def __init__(self, bot):
        self.bot = bot
        print("Thread Commands cog initialized!")

    @commands.command(name="commands")
    async def commands_list(self, ctx):
        """Show available commands"""
        if not is_privileged(ctx.author):
            return await ctx.reply("⚠️ Only Devs or Mods can use bot commands.")

        commands_list = """📋 **Available Commands:**

`!commands`
Show this help message

`!saveThread [thread_id] "nickname"`
Save a thread for monitoring
Example: `!saveThread 123456789 general-feedback`

`!sum "nickname" [timeframe]`
Generate a summary for a stored thread
Examples:
• `!sum general-feedback` - Last 24 hours
• `!sum general-feedback 3d` - Last 3 days
• `!sum general-feedback 1w` - Last week
• `!sum general-feedback 30d` - Last 30 days

`!listThreads`
Show all watched threads and their status

🔐 All commands require Mod or Dev role"""

        await ctx.reply(commands_list)

    @commands.command(name="listThreads")
    async def list_threads_command(self, ctx):
        """Show all watched threads and their status"""
        if not is_privileged(ctx.author):
            return await ctx.reply("⚠️ Only Devs or Mods can use this command.")

        try:
            threads = db.get_threads()
            if not threads:
                return await ctx.reply("No threads are currently being watched.")

            thread_list = ["📋 **Watched Threads:**\n"]
            for thread in threads:
                try:
                    # Try to fetch the thread to check if it still exists
                    channel = await ctx.guild.fetch_channel(thread.thread_id)
                    status = "🟢" if channel and isinstance(channel, discord.Thread) else "🔴"
                except (discord.NotFound, discord.Forbidden):
                    status = "🔴"

                thread_list.append(
                    f"{status} **{thread.nickname}**\n"
                    f"  • ID: {thread.thread_id}\n"
                    f"  • Created by: {thread.created_by}\n"
                    f"  • Created at: {thread.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                )

            await ctx.reply("\n".join(thread_list))
        except Exception as e:
            await ctx.reply(f"❌ Error listing threads: {str(e)}")

    @commands.command(name="saveThread")
    async def save_thread_command(self, ctx, thread_id: int, nickname: str):
        """Save a thread for monitoring"""
        if not can_manage_threads(ctx.author):
            return await ctx.reply("⚠️ Only Devs, Mods, or the server owner can save threads.")
        
        try:
            # Verify the thread exists by trying to fetch it
            thread = await ctx.guild.fetch_channel(thread_id)
            if not thread or not isinstance(thread, discord.Thread):
                return await ctx.reply("❌ Invalid thread ID or channel is not a thread.")
            
            # Save the thread first
            if not save_thread(thread_id, nickname, ctx.author):
                return await ctx.reply(f"❌ A thread with nickname '{nickname}' already exists.")
            
            progress_msg = await ctx.reply("📥 Starting message import...")
            try:
                count = await import_thread_history(thread, progress_msg)
                await progress_msg.edit(content=f"✅ Saved thread '{nickname}' and imported {count} messages.")
            except Exception as e:
                await progress_msg.edit(content=f"⚠️ Thread saved but error importing messages: {str(e)}")
        except discord.NotFound:
            await ctx.reply("❌ Thread not found. Please check the ID.")
        except discord.Forbidden:
            await ctx.reply("❌ I don't have permission to access that thread.")
        except Exception as e:
            await ctx.reply(f"❌ Error saving thread: {str(e)}")

    @commands.command(name="sum")
    async def sum_command(self, ctx, nickname: str, timeframe: str = None):
        """
        Generate a summary for a stored thread
        
        Examples:
        !sum general-feedback      - Last 24 hours
        !sum general-feedback 3d   - Last 3 days
        !sum general-feedback 1w   - Last week
        !sum general-feedback 30d  - Last 30 days
        """
        if not is_privileged(ctx.author):
            return await ctx.reply("⚠️ Only Devs or Mods can use this command.")
        
        thread = get_thread_by_name(nickname)
        if not thread:
            return await ctx.reply(f"❌ No thread found with nickname '{nickname}'.")
        
        try:
            start_date, end_date = parse_timeframe(timeframe)
            await ctx.reply(f"🧠 Generating summary for {format_timeframe(start_date, end_date)}... please wait.")
            
            summary = await summarize_thread(thread, timeframe)
            await ctx.reply(f"📋 **Summary ({format_timeframe(start_date, end_date)}):**\n{summary}")
        except Exception as e:
            await ctx.reply(f"❌ Error generating summary: {str(e)}")

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(ThreadCommands(bot))
    print("Thread Commands cog added!")