# Feedback Summarizer Bot

A Discord bot prototype that helps moderators and developers summarize feedback threads using AI (provider-agnostic).

---

## 🚀 Features
- Automatically records messages from specific threads
- Ignores non-text messages and commands
- Recognizes replies and timestamps
- Role-based permissions (Devs / Mods)
- Flexible AI provider system
- SQLAlchemy ORM for database flexibility
- Automatic message cleanup
- Thread descriptions for context-aware summaries
- Message deletion synchronization

---

## 🧩 Setup

### 1. Create a Discord Application and Bot
- Go to the [Discord Developer Portal](https://discord.com/developers/applications)
- Create a new application
- Add a bot user to the application
- Copy the bot token for use in the `.env` file
- Configure bot permissions (read/send messages, manage threads, etc.)

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/feedback-bot.git
cd feedback-bot
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
- Copy `.env.example` to `.env`
- Fill in your Discord bot token, OpenAI API key, and database URL
```
DISCORD_TOKEN=your_discord_bot_token_here
OPENAI_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///instance/feedback.db  # Default SQLite database
```

### 5. (Recommended) Create a Private Summaries Channel
- Create a private text channel in your Discord server (e.g., `#summaries`)
- Invite the bot to your server
- Ensure the bot has permissions to read and send messages in the summaries channel
- Use the bot commands from this channel to manage threads and generate summaries

> **Note:** Creating a private summaries channel is recommended for organization and privacy but is not required for the bot to function.

### 6. Run the Bot
```bash
python3 bot.py
```

---

### Example View

<img width="60%" alt="image" src="https://github.com/user-attachments/assets/11ae0e7c-6c77-45e6-b89d-e15d0af9da19" />



---

## 🤖 Commands

* `!commands` - Show all available commands
* `!saveThread [thread_id] "nickname"` - Save a thread for monitoring
* `!sum "nickname" [timeframe]` - Generate a summary for a stored thread
* `!listThreads` - Show all watched threads and their status
* `!setDescription "nickname" "description"` - Set context for a thread

Timeframe examples:
```
!sum general_feedback      # Last 24 hours (default)
!sum general_feedback 3d   # Last 3 days
!sum general_feedback 1w   # Last week
!sum general_feedback 30d  # Last 30 days
```

All commands require Mod or Dev role.

---

## ⚙️ Role Configuration

Role names for Devs and Mods are configurable in the `permissions.py` file:

```python
DEV_ROLES = ["Developer", "Dev"]
MOD_ROLES = ["Moderator", "Mod", "Admin"]
```

Modify these lists to match your server's specific role names to control access permissions.

---

## 📁 Project Structure

```
feedback-bot/
├── config/                 # Configuration files
│   ├── ai_config.py       # AI provider settings
│   ├── database.py        # Database configuration
│   └── prompts.py         # AI system prompts
├── models/                 # Database models
│   └── database.py        # SQLAlchemy models
├── services/              # Service layer
│   ├── ai/               # AI providers
│   │   ├── base.py       # Provider interface
│   │   └── openai_provider.py
│   └── summarizer.py     # Summary generation
├── utils/                 # Utility modules
├── instance/             # Instance-specific data
│   └── feedback.db       # SQLite database (if used)
└── commands/             # Bot commands
```

---

## 🧠 AI Provider System

The bot uses an abstracted AI provider system, making it easy to switch between different AI providers or add new ones.

### Supported Providers
- OpenAI (default)
- Anthropic (planned)
- Local LLM (planned)

### Adding a New Provider
1. Create a new provider class in `services/ai/`:
   ```python
   from .base import AIProvider
   
   class MyProvider(AIProvider):
       async def generate_summary(self, messages, prompt):
           # Implement summary generation
           pass
   ```

2. Add provider configuration in `config/ai_config.py`:
   ```python
   PROVIDER_SETTINGS = {
       AIProvider.MY_PROVIDER: {
           "model": "my-model",
           "temperature": 0.7
       }
   }
   ```

### Switching Providers
Update `DEFAULT_PROVIDER` in `config/ai_config.py`:
```python
DEFAULT_PROVIDER = AIProvider.OPENAI  # or your provider
```

---

## 🗄️ Database Configuration

The bot uses SQLAlchemy ORM for database operations, supporting both SQLite and PostgreSQL.

### SQLite (Default)
```
DATABASE_URL=sqlite:///instance/feedback.db
```

### PostgreSQL
```
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

Make sure to install the appropriate database driver:
- PostgreSQL: `pip install psycopg2-binary`

### Database Models
Database models are defined in `models/database.py`:
- Thread: Stores Discord thread information with descriptions
- Message: Stores thread messages with role information

Instance-specific data (like the database file) is stored in the `instance/` directory, which is excluded from version control.

---

## 📝 Thread Descriptions

Thread descriptions provide context for AI summaries, making them more accurate and relevant:

1. Save a thread: `!saveThread 123456789 alpha_feedback`
2. Add context: `!setDescription alpha_feedback "A place to provide feedback for the character 'Alpha'"`
3. Generate summary: `!sum alpha_feedback`

The AI will understand that the thread is about a specific topic (like character feedback), even if users don't explicitly mention it in every message.

---

## 🔄 Message Synchronization

The bot maintains synchronization between Discord and the database:
- New messages are saved to the database
- Edited messages are updated in the database
- Deleted messages are removed from the database

This ensures that summaries always reflect the current state of the thread.

---

## 🧹 Message Cleanup

Messages older than 30 days are automatically removed to maintain performance and relevance. This cleanup:
- Runs daily as a background task
- Only affects messages in the database
- Keeps Discord thread history intact

---

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
