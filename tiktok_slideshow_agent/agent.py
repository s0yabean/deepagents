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
from langchain_google_community import GoogleDriveSearchTool, GmailSearchTool 
# Note: GoogleDriveTool/GmailToolkit might require more setup (credentials.json). 
# For quickstart, we'll assume environment variables are handled or mock it if complex auth is needed.
# Using standard community tools as placeholders for now.

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
from tiktok_slideshow_agent.tools.agent_tools import render_slide, upload_and_save

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
# Specialist 4: Publisher
# ==============================================================================
publisher = {
    "name": "publisher",
    "description": "Uploads assets and logs the project.",
    "system_prompt": PUBLISHER_INSTRUCTIONS,
    "tools": [upload_and_save, GoogleDriveSearchTool(), GmailSearchTool()],
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
interrupt_points = ["publisher"] if enable_human_review else []

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
        publisher
    ],
    context_schema=AgentState,
    interrupt_on=interrupt_points, 
)
