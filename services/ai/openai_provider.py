from typing import List
from openai import OpenAI
from .base import AIProvider

class OpenAIProvider(AIProvider):
    """OpenAI implementation of the AI provider interface."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
    async def generate_summary(self, messages: List[str], prompt: str) -> str:
        """
        Generate a summary using OpenAI's chat completion API.
        
        Args:
            messages: List of formatted messages to summarize
            prompt: System prompt to guide the summary generation
            
        Returns:
            str: Generated summary
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "\n".join(messages)}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating summary with OpenAI: {e}")
            return f"Error generating summary: {str(e)}"