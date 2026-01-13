#!/usr/bin/env python3
"""
Test script to trigger Google Drive OAuth authentication.
This will open a browser for you to authenticate and create token.json
"""
import asyncio
from tiktok_slideshow_agent.tools.drive import GoogleDriveTool

async def test_auth():
    print("Testing Google Drive authentication...")
    print("A browser window will open - please log in and grant permissions.")

    drive = GoogleDriveTool()
    await drive._ensure_service()

    print("\n✅ Authentication successful!")
    print("token.json has been created.")
    print("\nYou can now run your agent normally.")

if __name__ == "__main__":
    asyncio.run(test_auth())
