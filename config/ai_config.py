from enum import Enum
from typing import Dict, Any

class AIProvider(Enum):
    """Available AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"  # For future implementation
    LOCAL_LLM = "local"      # For future implementation

# Default provider and model settings
DEFAULT_PROVIDER = AIProvider.OPENAI
DEFAULT_MODEL = "gpt-4"

# Provider-specific settings
PROVIDER_SETTINGS: Dict[AIProvider, Dict[str, Any]] = {
    AIProvider.OPENAI: {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1000
    },
    AIProvider.ANTHROPIC: {
        "model": "claude-2",
        "temperature": 0.7,
        "max_tokens": 1000
    },
    AIProvider.LOCAL_LLM: {
        "model": "llama2",
        "temperature": 0.7,
        "max_tokens": 1000
    }
}

# Environment variable names for API keys
API_KEY_ENV_VARS = {
    AIProvider.OPENAI: "OPENAI_KEY",
    AIProvider.ANTHROPIC: "ANTHROPIC_KEY",
    AIProvider.LOCAL_LLM: None  # Local models don't need API keys
}

def get_provider_settings(provider: AIProvider) -> Dict[str, Any]:
    """Get settings for a specific provider."""
    return PROVIDER_SETTINGS.get(provider, {})