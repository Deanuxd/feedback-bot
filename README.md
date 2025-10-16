# Feedback Summarizer Bot

A Discord bot prototype that helps moderators and developers summarize feedback threads using an LLM (OpenAI by default).

---

## 🚀 Features
- Automatically records messages from specific threads
- Ignores non-text messages and commands
- Recognizes replies and timestamps
- Role-based permissions (Devs / Mods)
- Easily extendable with other AI models
- SQLAlchemy ORM for database flexibility

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
   DATABASE_URL=sqlite:///feedback.db  # Default SQLite database
   ```

4. Run the bot:
   ```bash
   python3 bot.py
   ```

---

## 🤖 Commands

* `!commands` - Show all available commands
* `!saveThread [thread_id] "nickname"` - Save a thread for monitoring
* `!sum "nickname"` - Generate a summary for a stored thread
* `!listThreads` - Show all watched threads and their status

All commands require Mod or Dev role.

---

## 🗄️ Database Configuration

The bot uses SQLAlchemy ORM for database operations, which means you can easily switch between different database engines without changing any code.

### SQLite (Default)
```
DATABASE_URL=sqlite:///feedback.db
```

### PostgreSQL
```
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

Make sure to install the appropriate database driver:
- PostgreSQL: `pip install psycopg2-binary`

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

## 🧠 Future Plans
* Support for multiple threads
* Date-based summaries
* Image/attachment processing
* Database logging
* Custom AI model support

---

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.