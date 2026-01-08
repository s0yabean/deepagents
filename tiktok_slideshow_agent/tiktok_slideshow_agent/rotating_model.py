
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
        super().__init__(google_api_key=api_keys[0], api_keys=api_keys, **kwargs)
        self.current_key_index = 0
        
        print(f"🔑 [DEBUG] Initialized RotatingGeminiModel with {len(api_keys)} API key(s)")

    def _rotate_key(self) -> bool:
        """Rotates to the next available API key. Returns True if successful."""
        next_index = (self.current_key_index + 1) % len(self.api_keys)
        
        if next_index == self.current_key_index and len(self.api_keys) == 1:
            return False 
            
        self.current_key_index = next_index
        new_key = self.api_keys[self.current_key_index]
        
        self.google_api_key = new_key
        
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
        attempts = 0
        max_attempts = len(self.api_keys) * 2
        
        while attempts < max_attempts:
            try:
                result = super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
                if type(result).__name__ == 'ClientResponse' or not hasattr(result, 'generations'):
                    raise TypeError(f"Malformed result: {type(result).__name__}")
                return result
            except (Exception, TypeError) as e:
                if self._should_rotate(e):
                    if self._rotate_key():
                        attempts += 1
                        continue
                raise e
        raise Exception("Max retry attempts exceeded.")

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Override _agenerate to handle rate limits asynchronously."""
        attempts = 0
        max_attempts = len(self.api_keys) * 2
        
        while attempts < max_attempts:
            try:
                result = await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)
                if type(result).__name__ == 'ClientResponse' or not hasattr(result, 'generations'):
                    raise TypeError(f"Malformed result: {type(result).__name__}")
                return result
            except (Exception, TypeError) as e:
                if self._should_rotate(e):
                    if self._rotate_key():
                        attempts += 1
                        continue
                raise e
        raise Exception("Max retry attempts exceeded.")

    def _should_rotate(self, e: Exception) -> bool:
        error_str = str(e).lower()
        if "clientresponse" in error_str or "not subscriptable" in error_str:
            return True
        if "429" in error_str or "resource_exhausted" in error_str or "quota" in error_str:
            return True
        if isinstance(e, google.api_core.exceptions.ResourceExhausted):
            return True
        return False
