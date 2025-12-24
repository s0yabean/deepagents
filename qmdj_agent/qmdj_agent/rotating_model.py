
import logging
from typing import List, Optional, Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
import google.api_core.exceptions

logger = logging.getLogger(__name__)

class RotatingGeminiModel(ChatGoogleGenerativeAI):
    """
    A wrapper around ChatGoogleGenerativeAI that automatically rotates through
    a list of API keys when rate limits (429) are encountered.
    """
    api_keys: List[str]
    current_key_index: int = 0
    rotation_strategy: str = "round-robin"

    def __init__(self, api_keys: List[str], **kwargs):
        if not api_keys:
            raise ValueError("At least one API key must be provided.")
        
        # Initialize with the first key
        # Pass api_keys to super().__init__ because it's a field of this Pydantic model
        super().__init__(google_api_key=api_keys[0], api_keys=api_keys, **kwargs)
        # self.api_keys is already set by super().__init__ via Pydantic logic
        self.current_key_index = 0
        
        print(f"🔑 Initialized RotatingGeminiModel with {len(api_keys)} API key(s)")

    def _rotate_key(self) -> bool:
        """Rotates to the next available API key. Returns True if successful, False if all keys exhausted."""
        next_index = (self.current_key_index + 1) % len(self.api_keys)
        
        # If we've cycled back to the start in a short time, we might be out of keys.
        # For simplicity, we just rotate to the next one.
        # A more complex implementation would track failed keys per request.
        
        if next_index == self.current_key_index and len(self.api_keys) == 1:
            return False # Only one key, cannot rotate
            
        self.current_key_index = next_index
        new_key = self.api_keys[self.current_key_index]
        
        # Update the Pydantic field
        self.google_api_key = new_key
        # Also update the client if it's already initialized (LangChain implementation detail)
        # ChatGoogleGenerativeAI usually re-initializes client on access or we might need to force it.
        # But updating the pydantic field is the standard way.
        
        print(f"🔄 Rotated to API key #{self.current_key_index + 1}/{len(self.api_keys)}")
        return True

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Override _generate to handle rate limits."""
        
        # Try up to len(api_keys) times
        attempts = 0
        max_attempts = len(self.api_keys) * 2 # Allow some retries
        
        while attempts < max_attempts:
            try:
                return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
            except Exception as e:
                # Check for Rate Limit errors
                is_rate_limit = False
                error_str = str(e).lower()
                
                if "429" in error_str:
                    is_rate_limit = True
                elif "resource_exhausted" in error_str:
                    is_rate_limit = True
                elif "quota" in error_str and "exceeded" in error_str:
                    is_rate_limit = True
                elif isinstance(e, google.api_core.exceptions.ResourceExhausted):
                    is_rate_limit = True
                
                if is_rate_limit:
                    print(f"⚠️ Rate limit hit on API key #{self.current_key_index + 1}")
                    if self._rotate_key():
                        attempts += 1
                        continue # Retry with new key
                    else:
                        print("❌ All API keys exhausted or rotation failed.")
                        raise e
                else:
                    # Not a rate limit error, raise immediately
                    raise e
        
        raise Exception("Max retry attempts exceeded due to rate limits.")
