import os
from typing import List, Optional
from services.ai.base import AIProvider
from services.ai.openai_provider import OpenAIProvider
from config.ai_config import AIProvider as ProviderType, get_provider_settings, API_KEY_ENV_VARS

class SummarizerService:
    """Service for generating summaries using configured AI provider."""
    
    def __init__(self, provider_type: ProviderType = ProviderType.OPENAI):
        """
        Initialize the summarizer service.
        
        Args:
            provider_type: Type of AI provider to use (default: OPENAI)
        """
        self.provider = self._initialize_provider(provider_type)
        
    def _initialize_provider(self, provider_type: ProviderType) -> AIProvider:
        """
        Initialize the specified AI provider.
        
        Args:
            provider_type: Type of AI provider to initialize
            
        Returns:
            AIProvider: Initialized provider instance
            
        Raises:
            ValueError: If provider type is not supported or API key is missing
        """
        settings = get_provider_settings(provider_type)
        api_key_var = API_KEY_ENV_VARS.get(provider_type)
        
        if provider_type == ProviderType.OPENAI:
            if not api_key_var or not os.getenv(api_key_var):
                raise ValueError(f"Missing API key for {provider_type.value}. Set {api_key_var} environment variable.")
            return OpenAIProvider(
                api_key=os.getenv(api_key_var),
                model=settings.get("model", "gpt-4")
            )
        # Add other provider initializations here as they're implemented
        else:
            raise ValueError(f"Unsupported AI provider: {provider_type.value}")
    
    async def generate_summary(self, 
                             messages: List[str], 
                             prompt: str,
                             provider_type: Optional[ProviderType] = None) -> str:
        """
        Generate a summary using the configured AI provider.
        
        Args:
            messages: List of formatted messages to summarize
            prompt: System prompt to guide the summary generation
            provider_type: Optional override for provider type
            
        Returns:
            str: Generated summary
        """
        if provider_type and provider_type != self.provider_type:
            # Switch provider if a different one is requested
            self.provider = self._initialize_provider(provider_type)
            
        return await self.provider.generate_summary(messages, prompt)