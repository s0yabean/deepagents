import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from tiktok_slideshow_agent.tools.vision_tool import select_best_fitting_image

async def main():
    print(" successfully imported select_best_fitting_image tool.")
    print("Tool Name:", select_best_fitting_image.name)
    print("Tool Description:", select_best_fitting_image.description)
    
    # We won't actually call it to avoid API costs/Mocking complexity in this simple check,
    # but confirming it imports and has correct metadata is a good first step.
    
if __name__ == "__main__":
    asyncio.run(main())
