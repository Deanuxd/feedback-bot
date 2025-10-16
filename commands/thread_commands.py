import discord
from discord.ext import commands
from permissions import can_manage_threads, is_privileged
from utils.thread_store import save_thread, get_thread_by_name
from utils.logging_utils import log_message
from utils.db import db, Session, Thread, Message
from utils.migrate import migrate_log_to_db
from sqlalchemy.exc import SQLAlchemyError
from openai import OpenAI
import os

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

BACKGROUND_PROMPT = """
You are an assistant that summarizes and analyzes user feedback from a Discord thread.
The messages are written by users/mods discussing features, issues, and ideas.
- Write concise, neutral summaries unless asked otherwise.
- Focus on grouping similar feedback together.
- Ignore jokes or unrelated chatter unless directly relevant.
- Maintain a professional tone suitable for a product team review.
- Take into account any replies to a message that contain important information regarding the original message, especially from Mods.
- Pay special attention to feedback from users with [Mod] or [Dev] roles, as they often provide important context or confirmations.
"""

async def summarize_thread(thread_info):
    """Generate a summary for the specified thread using OpenAI."""
    try:
        # Get all messages for the thread
        with Session() as session:
            messages = session.query(Message).filter(
                Message.thread_id == thread_info.thread_id
            ).order_by(Message.created_at.asc()).all()

            if not messages:
                return "No messages found in this thread."

            # Format messages for the AI
            formatted_messages = []
            for msg in messages:
                role_prefix = f"[{msg.role}] " if msg.role else ""
                formatted_messages.append(f"{role_prefix}{msg.author}: {msg.content}")

            message_text = "\n".join(formatted_messages)

            # Generate summary using OpenAI
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": BACKGROUND_PROMPT},
                    {"role": "user", "content": f"Summarize the following feedback thread:\n\n{message_text}"}
                ],
                max_tokens=1000,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error generating summary: {e}")
        return f"Error generating summary: {str(e)}"

async def import_thread_history(thread: discord.Thread, progress_message = None):
    """Import all messages from a thread's history."""
    messages_imported = 0
    
    try:
        with Session() as session:
            async for msg in thread.history(limit=None, oldest_first=True):
                if not msg.author.bot and msg.content.strip():
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
            
            session.commit()
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

`!sum "nickname"`
Generate a summary for a stored thread
Example: `!sum general-feedback`

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
            with Session() as session:
                threads = session.query(Thread).all()
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
    async def sum_command(self, ctx, nickname: str):
        """Generate a summary for a stored thread"""
        if not is_privileged(ctx.author):
            return await ctx.reply("⚠️ Only Devs or Mods can use this command.")
        
        thread = get_thread_by_name(nickname)
        if not thread:
            return await ctx.reply(f"❌ No thread found with nickname '{nickname}'.")
        
        try:
            await ctx.reply("🧠 Generating summary... please wait.")
            summary = await summarize_thread(thread)
            await ctx.reply(f"📋 **Summary:**\n{summary}")
        except Exception as e:
            await ctx.reply(f"❌ Error generating summary: {str(e)}")

async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(ThreadCommands(bot))
    print("Thread Commands cog added!")