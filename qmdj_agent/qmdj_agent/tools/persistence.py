"""Tools for file-based data persistence (Shared Memory)."""

import os
import json
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

CACHE_ROOT = ".qmdj_cache"

# Ensure cache root exists
if not os.path.exists(CACHE_ROOT):
    os.makedirs(CACHE_ROOT)

@tool(parse_docstring=True)
def save_to_file(data: str, filename: str, thread_id: str = None, config: RunnableConfig = None) -> str:
    """Save data (typically a JSON string) to a file in the shared cache.
    
    Use this to persist large datasets like `chart_json` or `energy_json` so other agents can read them.
    
    Args:
        data: The content to save (usually a JSON string).
        filename: The name of the file (e.g., 'chart.json', 'energy.json').
        thread_id: Optional. Manually specify the thread ID. If None, uses the current thread's config.
        config: The configuration including thread_id (injected automatically).
    """
    try:
        # Determine thread-specific path
        if not thread_id:
            thread_id = config.get("configurable", {}).get("thread_id", "default_thread") if config else "default_thread"
            
        thread_dir = os.path.join(CACHE_ROOT, thread_id)
        
        if not os.path.exists(thread_dir):
            os.makedirs(thread_dir)
            
        filepath = os.path.join(thread_dir, filename)
        
        # Verify it's a valid JSON string if it looks like one (simple check)
        if data.strip().startswith("{") or data.strip().startswith("["):
            try:
                # Validate JSON structure (parsing check)
                _ = json.loads(data)
            except json.JSONDecodeError as e:
                return f"Error: Data was not valid JSON. Save aborted. Error: {str(e)}"

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)
            
        return f"Success: Data saved to {filepath} (Thread ID: {thread_id})."
        
    except Exception as e:
        return f"Error saving file to {filepath} (Thread ID: {thread_id}): {str(e)}"

@tool(parse_docstring=True)
def read_from_file(filename: str, thread_id: str = None, config: RunnableConfig = None) -> str:
    """Read data from a file in the shared cache.
    
    Use this to retrieve large datasets like `chart_json` that were saved by other agents.
    
    Args:
        filename: The name of the file to read (e.g., 'chart.json').
        thread_id: Optional. Manually specify the thread ID. If None, uses the current thread's config.
        config: The configuration including thread_id (injected automatically).
    """
    try:
        if not thread_id:
            thread_id = config.get("configurable", {}).get("thread_id", "default_thread") if config else "default_thread"
            
        thread_dir = os.path.join(CACHE_ROOT, thread_id)
        filepath = os.path.join(thread_dir, filename)
        
        if not os.path.exists(filepath):
            return f"Error: File '{filename}' not found in thread '{thread_id}'. Attempted path: {filepath}. Please ensure the previous agent saved it correctly."
            
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
            
    except Exception as e:
        return f"Error reading file: {str(e)}"
