# Changelog

All notable changes to the Feedback Bot project will be documented in this file.

## [1.3.0] - 2025-11-08

### Added
- Thread description feature
  - Added description field to Thread model
  - New `!setDescription` command to set context for threads
  - Descriptions are included in AI prompts for better summaries
  - Migration script for adding description column to existing databases
- Message deletion synchronization
  - Messages deleted in Discord are now removed from the database
  - Ensures summaries only include current messages
- Long summary handling
  - Summaries exceeding Discord's 2000 character limit are split into multiple messages
  - Ensures complete summaries for longer timeframes

### Changed
- Improved database operations
  - Added get_threads() method for listing all threads
  - Added delete_message() method for removing deleted messages
  - Updated ThreadInfo dataclass to include description field
- Enhanced summary generation
  - Thread descriptions provide context for AI summaries
  - Better handling of thread-specific topics

## [1.2.1] - 2025-10-24

### Changed
- Reorganized database structure
  - Moved models to `models/database.py`
  - Moved configuration to `config/database.py`
  - Created `instance/` directory for user-specific data
  - Updated .gitignore to exclude instance files
- Improved project organization
  - Separated models from database operations
  - Instance-specific files now in instance/ directory
  - Better separation of concerns

## [1.2.0] - 2025-10-24

### Added
- AI Provider abstraction layer
  - Abstract base class for AI providers
  - Provider-specific implementations (OpenAI)
  - Easy extensibility for new providers
- Configuration system
  - New `config/` directory for all configurations
  - AI provider settings in `config/ai_config.py`
  - Prompts moved to `config/prompts.py`
- Summarizer service
  - Provider-agnostic summary generation
  - Easy provider switching
  - Consistent interface across providers

### Changed
- Moved configuration to dedicated files
  - AI prompts now in config/prompts.py
  - Provider settings in config/ai_config.py
- Refactored summary generation to use provider abstraction
- Improved project structure with services/ directory

### Developer Notes
- Add new AI providers by implementing AIProvider interface
- Configure providers in config/ai_config.py
- Switch providers by updating DEFAULT_PROVIDER

## [1.1.1] - 2025-10-24

### Changed
- Moved summary prompts to separate `summary_prompt.py` file
  - Added DEFAULT_PROMPT for standard summaries
  - Added CUSTOM_PROMPT_1 as an alternative template
  - Makes it easier for devs to modify prompts
  - Removed hardcoded prompt from bot.py

## [1.1.0] - 2025-10-22

### Added
- Time-scoped summaries
  - Default scope of last 24 hours
  - Support for custom timeframes (3d, 1w, 30d)
  - Human-readable timeframe formatting
  - Examples in help command
- Automatic message cleanup system
  - Messages older than 30 days are automatically removed
  - Cleanup runs daily as a background task
  - Cleanup results are logged for monitoring

### Changed
- Enhanced `!sum` command with timeframe parameter
- Updated help text with timeframe examples
- Improved summary formatting with timeframe context

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