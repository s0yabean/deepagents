
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
        
        print(f"🔑 [DEBUG] Initialized RotatingGeminiModel with {len(api_keys)} API key(s)")
        print(f"🔑 [DEBUG] Active Key: ...{self.api_keys[self.current_key_index][-6:]}")

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
                # We must catch the specific TypeError that happens inside langchain_google_genai
                # when the SDK returns a leaked ClientResponse object.
                # This happens deep in the stack: _generate_response_from_error -> hasattr(response, "json")
                result = super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
                
                # Also check for malformed result if no exception was raised
                if type(result).__name__ == 'ClientResponse' or not hasattr(result, 'generations'):
                    print(f"⚠️ Received malformed result ({type(result).__name__}). Raising TypeError to trigger rotation.")
                    raise TypeError(f"Malformed result: {type(result).__name__}")
                    
                return result
            except (Exception, TypeError) as e:
                # Check if this is the specific ClientResponse error
                is_leaked_response = False
                if "ClientResponse" in str(e) or "not subscriptable" in str(e):
                    is_leaked_response = True
                
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
                
                if is_rate_limit or is_leaked_response:
                    reason = "Rate limit" if is_rate_limit else "Leaked ClientResponse"
                    print(f"⚠️ {reason} hit on API key #{self.current_key_index + 1}")
                    if self._rotate_key():
                        attempts += 1
                        continue # Retry with new key
                    else:
                        print(f"❌ All API keys exhausted or rotation failed for {reason}.")
                        raise e
                else:
                    # Not a rate limit or leak error, raise immediately
                    raise e
        
        raise Exception("Max retry attempts exceeded due to rate limits.")

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Override _agenerate to handle rate limits asynchronously."""
        
        # Try up to len(api_keys) times
        attempts = 0
        max_attempts = len(self.api_keys) * 2 # Allow some retries
        
        while attempts < max_attempts:
            try:
                # We must catch the specific TypeError that happens inside langchain_google_genai
                # when the SDK returns a leaked ClientResponse object.
                try:
                    result = await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)
                    
                    # Check for malformed result if no exception was raised
                    if type(result).__name__ == 'ClientResponse' or not hasattr(result, 'generations'):
                        print(f"⚠️ Received malformed result ({type(result).__name__}). Raising TypeError to trigger rotation.")
                        raise TypeError(f"Malformed result: {type(result).__name__}")
                        
                    return result
                except (Exception, TypeError) as e:
                    # Check if this is the specific ClientResponse error
                    is_leaked_response = False
                    if "ClientResponse" in str(e) or "not subscriptable" in str(e):
                        is_leaked_response = True
                        print(f"⚠️ Caught ClientResponse error inside SDK: {e}")
                        raise TypeError("ClientResponse error caught") # Re-raise as TypeError to trigger rotation below
                    
                    raise e # Re-raise other errors
                    
            except (Exception, TypeError) as e:
                # Check for malformed response (ClientResponse object leaking)
                is_leaked_response = False
                if "ClientResponse" in str(e) or "not subscriptable" in str(e):
                    is_leaked_response = True
                
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
                
                if is_rate_limit or is_leaked_response:
                    reason = "Rate limit" if is_rate_limit else "Leaked ClientResponse"
                    print(f"⚠️ {reason} hit on API key #{self.current_key_index + 1}")
                    if self._rotate_key():
                        attempts += 1
                        continue # Retry with new key
                    else:
                        print(f"❌ All API keys exhausted or rotation failed for {reason}.")
                        raise e
                else:
                    # Not a rate limit or leak error, raise immediately
                    raise e
        
        raise Exception("Max retry attempts exceeded due to rate limits.")
