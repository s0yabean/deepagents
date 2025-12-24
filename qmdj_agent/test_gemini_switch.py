
import sys
import os
sys.path.append(os.getcwd())

from agent import agent, model
from qmdj_agent.rotating_model import RotatingGeminiModel

print("Agent initialized.")
# Check if the model is correctly set
if isinstance(model, RotatingGeminiModel):
    print("SUCCESS: Agent is using RotatingGeminiModel.")
    print(f"Model Name: {model.model}")
    print(f"Loaded Keys: {len(model.api_keys)}")
else:
    print(f"FAILURE: Agent is using {type(model)}")

import asyncio

async def test_async_invoke():
    print("\nTesting async invocation...")
    try:
        # We use a simple prompt to test connectivity
        response = await model.ainvoke("Hello, are you ready?")
        print(f"Async Response: {response.content}")
        print("SUCCESS: Async invocation worked.")
    except Exception as e:
        print(f"Async Error: {e}")

try:
    # Dry run invocation to check for API key issues
    # We won't actually wait for a full response to save time/cost, just check init
    print("Agent is ready for invocation.")
    
    # Run async test
    asyncio.run(test_async_invoke())
    
except Exception as e:
    print(f"Error during agent check: {e}")
