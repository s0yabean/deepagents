"""TikTok Slideshow Agent - Deep Agent Architecture."""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

# Import Deep Agent Factory
# Assuming deepagents is installed or available in path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../qmdj_agent/.venv/lib/python3.12/site-packages"))
from deepagents import create_deep_agent

# Import LangChain Community Tools
from langchain_community.tools import TavilySearchResults
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import build_resource_service, get_google_credentials
# Note: Gmail/Google Drive tools require OAuth credentials (credentials.json and token.json)
# Make sure you have proper Google Cloud project setup with Gmail API enabled

# Import State
from tiktok_slideshow_agent.state import AgentState

# Import Prompts
from tiktok_slideshow_agent.prompts.orchestrator import ORCHESTRATOR_INSTRUCTIONS
from tiktok_slideshow_agent.prompts.specialists import (
    HOOK_AGENT_INSTRUCTIONS,
    STRATEGIST_INSTRUCTIONS,
    DESIGNER_INSTRUCTIONS,
    PUBLISHER_INSTRUCTIONS,
    QA_INSTRUCTIONS
)

# Import Tools
from tiktok_slideshow_agent.tools.agent_tools import render_slide, save_locally

# ==============================================================================
# Specialist 1: Hook Agent
# ==============================================================================
hook_agent = {
    "name": "hook-agent",
    "description": "Generates and selects the best hook for the slideshow.",
    "system_prompt": HOOK_AGENT_INSTRUCTIONS,
    "tools": [TavilySearchResults(max_results=3)], 
}

# ==============================================================================
# Specialist 2: Content Strategist
# ==============================================================================
content_strategist = {
    "name": "content-strategist",
    "description": "Writes the full script for the slideshow.",
    "system_prompt": STRATEGIST_INSTRUCTIONS,
    "tools": [], # Pure LLM task
}

# ==============================================================================
# Specialist 3: Visual Designer
# ==============================================================================
def get_visual_designer():
    # We'll use a placeholder and have the orchestrator or a middleware inject it,
    # or just accept that it's loaded when the subagent is initialized.
    # To avoid blocking at IMPORT time, we keep this as a function.
    
    return {
        "name": "visual-designer",
        "description": "Selects images and renders the final slides.",
        "system_prompt": DESIGNER_INSTRUCTIONS, # Use raw instructions
        "tools": [render_slide], # search_images removed in favor of filesystem tools
    }

# ==============================================================================
# Custom Google Drive Upload Tool
# ==============================================================================
@tool
def upload_to_google_drive(file_paths: list[str], folder_id: str = "1HQv0qrW1AUlUs2PWM3cQ572NyqonpLks") -> str:
    """Upload multiple files to Google Drive.

    Args:
        file_paths: List of local paths to the files to upload
        folder_id: Google Drive folder ID to upload to (defaults to TikTok Reels folder)

    Returns:
        String with the status and shareable link to the folder
    """
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    try:
        # Get credentials
        creds = get_google_credentials(
            scopes=["https://www.googleapis.com/auth/drive.file"],
            token_file="token_drive.json"
        )

        service = build('drive', 'v3', credentials=creds)
        uploaded_files = []

        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
                
            file_metadata = {'name': os.path.basename(file_path)}
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaFileUpload(file_path, resumable=True)
            file_resp = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            uploaded_files.append(file_resp.get('webViewLink'))

        folder_link = f"https://drive.google.com/drive/folders/{folder_id}"
        return f"Successfully uploaded {len(uploaded_files)} files. Folder Link: {folder_link}"
    except Exception as e:
        return f"Error uploading to Google Drive: {str(e)}"

# ==============================================================================
# Specialist 4: Publisher
# ==============================================================================
def get_publisher():
    """Initialize publisher with Gmail toolkit."""
    try:
        # Initialize Gmail toolkit
        gmail_creds = get_google_credentials(
            scopes=["https://www.googleapis.com/auth/gmail.modify"],
            token_file="token_gmail.json"
        )
        gmail_api_resource = build_resource_service(credentials=gmail_creds)
        gmail_toolkit = GmailToolkit(api_resource=gmail_api_resource)
        gmail_tools = gmail_toolkit.get_tools()

        return {
            "name": "publisher",
            "description": "Uploads assets and logs the project.",
            "system_prompt": PUBLISHER_INSTRUCTIONS,
            "tools": [save_locally, upload_to_google_drive] + gmail_tools,
        }
    except Exception as e:
        # Fallback if credentials not configured
        print(f"Warning: Could not initialize Google tools: {e}")
        return {
            "name": "publisher",
            "description": "Uploads assets and logs the project.",
            "system_prompt": PUBLISHER_INSTRUCTIONS,
            "tools": [save_locally],
        }

# ==============================================================================
# Specialist 5: QA Specialist
# ==============================================================================
qa_specialist = {
    "name": "qa-specialist",
    "description": "Final quality control check.",
    "system_prompt": QA_INSTRUCTIONS,
    "tools": [], # Pure LLM evaluation
}

# ==============================================================================
# Model Configuration
# ==============================================================================
load_dotenv()

# Use Gemini 3 Flash Preview as requested
model = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0.7)


# ==============================================================================
# Create the Deep Agent
# ==============================================================================
from tiktok_slideshow_agent.state import AgentState
from deepagents.backends import CompositeBackend, StateBackend, FilesystemBackend

# Define the backend to route /image_library/ to the real disk
def get_backend(rt):
    return CompositeBackend(
        default=StateBackend(rt),
        routes={
            "/image_library/": FilesystemBackend(
                root_dir="/Users/mindreader/Desktop/deepagents-quickstarts/tiktok_slideshow_agent/image_library",
                virtual_mode=True
            ),
        }
    )

# Check for Human-in-the-Loop config
enable_human_review = os.getenv("ENABLE_HUMAN_REVIEW", "False").lower() == "true"
interrupt_points = {"publisher": {}} if enable_human_review else {}

agent = create_deep_agent(
    model=model,
    tools=[], # Orchestrator tools (if any)
    system_prompt=ORCHESTRATOR_INSTRUCTIONS,
    backend=get_backend,
    subagents=[
        hook_agent,
        content_strategist,
        get_visual_designer(),
        qa_specialist,
        get_publisher()
    ],
    context_schema=AgentState,
    interrupt_on=interrupt_points,
)
