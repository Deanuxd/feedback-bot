import discord
from discord.ext import commands
from permissions import can_manage_threads, is_privileged
from utils.thread_store import save_thread, get_thread_by_name
from utils.logging_utils import log_message
from utils.migrate import migrate_log_to_db
from utils.time_utils import parse_timeframe, format_timeframe
from config.prompts import DEFAULT_PROMPT
from config.database import db, Thread, Message
from services.summarizer import SummarizerService
import os
from sqlalchemy.orm import Session

# Initialize summarizer service
summarizer = SummarizerService()

class ThreadCommands(commands.Cog):
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

!commands
Show this help message

!saveThread [thread_id] "nickname"
Save a thread for monitoring

!sum "nickname" [timeframe]
Generate a summary for a stored thread

!listThreads
Show all watched threads and their status

!setDescription "nickname" "description"
Set or update the description for a thread

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

    @commands.command(name="setDescription")
    async def set_description_command(self, ctx, nickname: str, *, description: str):
        """Set or update the description for a thread."""
        if not can_manage_threads(ctx.author):
            return await ctx.reply("⚠️ Only Devs, Mods, or the server owner can set thread descriptions.")
        
        thread = get_thread_by_name(nickname)
        if not thread:
            return await ctx.reply(f"❌ No thread found with nickname '{nickname}'.")
        
        try:
            with db.Session() as session:
                db_thread = session.query(Thread).filter(Thread.thread_id == thread.thread_id).first()
                if db_thread:
                    db_thread.description = description
                    session.commit()
                    await ctx.reply(f"✅ Description updated for thread '{nickname}'.")
                else:
                    await ctx.reply(f"❌ Thread '{nickname}' not found in database.")
        except Exception as e:
            await ctx.reply(f"❌ Error updating description: {str(e)}")

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
            
            # Include thread description in the prompt if available
            prompt = DEFAULT_PROMPT
            if thread.description:
                prompt = f"{thread.description}\n\n{prompt}"
            
            summary = await summarize_thread(thread, timeframe, prompt)
            
            # Split long summaries into multiple messages (Discord has a 2000 character limit)
            header = f"📋 **Summary ({format_timeframe(start_date, end_date)}):**\n"
            max_length = 2000 - len(header)
            
            if len(summary) <= max_length:
                await ctx.reply(f"{header}{summary}")
            else:
                # Send the header with the first part
                await ctx.reply(f"{header}{summary[:max_length]}")
                
                # Send the rest in chunks
                remaining = summary[max_length:]
                chunk_size = 1990  # Leave some room for "..." prefix
                
                for i in range(0, len(remaining), chunk_size):
                    chunk = remaining[i:i+chunk_size]
                    await ctx.reply(f"...{chunk}")
        except Exception as e:
            await ctx.reply(f"❌ Error generating summary: {str(e)}")

async def summarize_thread(thread_info, timeframe=None, prompt=DEFAULT_PROMPT):
    """Generate a summary for the specified thread using configured AI provider."""
    try:
        # Parse timeframe and get date range
        start_date, end_date = parse_timeframe(timeframe)
        
        # Get messages for the thread within the timeframe
        with db.Session() as session:
            messages = session.query(Message).filter(
                Message.thread_id == thread_info.thread_id,
                Message.created_at >= start_date,
                Message.created_at <= end_date
            ).order_by(Message.created_at.asc()).all()

            if not messages:
                return f"No messages found in this thread for {format_timeframe(start_date, end_date)}."

            # Format messages for the AI
            formatted_messages = []
            for msg in messages:
                role_prefix = f"[{msg.role}] " if msg.role else ""
                formatted_messages.append(f"{role_prefix}{msg.author}: {msg.content}")

            # Generate summary using configured AI provider
            return await summarizer.generate_summary(formatted_messages, prompt)

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
            
    except Exception as e:
        print(f"Database error during import: {e}")
        raise Exception("Database error during message import")

async def setup(bot):
    await bot.add_cog(ThreadCommands(bot))
    print("Thread Commands cog added!")