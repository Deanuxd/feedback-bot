# Changelog

All notable changes to the Feedback Bot project will be documented in this file.

## [1.0.0] - 2025-10-16

### Added
- SQLAlchemy ORM integration for database operations
- Support for both SQLite and PostgreSQL databases
- Role tracking for messages (Mod, Dev)
- New commands:
  - `!commands` - Show available commands
  - `!listThreads` - Show all watched threads with status
  - `!saveThread` - Save and monitor a thread
  - `!sum` - Generate thread summary using GPT-4
- Proper project structure:
  - utils/ directory for helper modules
  - commands/ directory for bot commands
  - Separated database, logging, and permissions logic
- Environment configuration:
  - .env.example template
  - Database URL configuration
  - OpenAI API key configuration
- Documentation:
  - Comprehensive README.md
  - MIT License
  - This changelog

### Changed
- Migrated from direct SQLite to SQLAlchemy ORM
- Improved thread monitoring with status indicators
- Enhanced message logging with role information
- Better error handling and user feedback
- Organized code into proper modules

### Technical Details
- Database Schema:
  - threads table with nickname and metadata
  - messages table with role and reply tracking
  - Proper indexes for performance
- Command System:
  - Implemented as Discord.py Cog
  - Role-based permission system
  - Async/await for all operations
- AI Integration:
  - GPT-4 for summarization
  - Custom prompt for feedback analysis
  - Role-aware message formatting

### Developer Notes
- The bot uses SQLAlchemy for database abstraction
- Easy to switch between SQLite and PostgreSQL
- Role information is preserved in summaries
- All commands require Mod or Dev role
- Thread status shows 🟢 for active, 🔴 for inaccessible