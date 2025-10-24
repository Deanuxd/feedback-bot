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

---

## 🧩 Setup
1. Clone the repo:
   ```bash
   git clone https://github.com/yourusername/feedback-bot.git
   cd feedback-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and add your tokens:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   OPENAI_KEY=your_openai_api_key_here
   DATABASE_URL=sqlite:///instance/feedback.db  # Default SQLite database
   ```

4. Run the bot:
   ```bash
   python3 bot.py
   ```

---

## 🤖 Commands

* `!commands` - Show all available commands
* `!saveThread [thread_id] "nickname"` - Save a thread for monitoring
* `!sum "nickname" [timeframe]` - Generate a summary for a stored thread
* `!listThreads` - Show all watched threads and their status

Timeframe examples:
```
!sum general_feedback      # Last 24 hours (default)
!sum general_feedback 3d   # Last 3 days
!sum general_feedback 1w   # Last week
!sum general_feedback 30d  # Last 30 days
```

All commands require Mod or Dev role.

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
- Thread: Stores Discord thread information
- Message: Stores thread messages with role information

Instance-specific data (like the database file) is stored in the `instance/` directory, which is excluded from version control.

---

## ⚙️ Configuration

All configuration files are in the `config/` directory:

- `prompts.py` - AI system prompts
- `ai_config.py` - AI provider settings
- `database.py` - Database configuration

---

## 🔐 Permissions

By default, only users with **Mod** or **Dev** roles (configurable in `permissions.py`) can:
* Use any bot commands
* Generate summaries
* Manage threads

The following roles are recognized:
* Dev roles: "Developer", "Dev"
* Mod roles: "Moderator", "Mod", "Admin"

---

## 🧹 Message Cleanup

Messages older than 30 days are automatically removed to maintain performance and relevance. This cleanup:
- Runs daily as a background task
- Only affects messages in the database
- Keeps Discord thread history intact

---

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.