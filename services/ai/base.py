from abc import ABC, abstractmethod
from typing import List

class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def generate_summary(self, messages: List[str], prompt: str) -> str:
        """
        Generate a summary from a list of messages using the provided prompt.
        
        Args:
            messages: List of formatted messages to summarize
            prompt: System prompt to guide the summary generation
            
        Returns:
            str: Generated summary
        """
        pass