"""TikTok Slideshow Agent - Deep Agent Architecture."""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

# Import Deep Agent Factory
# Assuming deepagents is installed or available in path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../qmdj_agent/.venv/lib/python3.12/site-packages"))
from deepagents import create_deep_agent

# Import Tavily Search Tool
from langchain_tavily import TavilySearch
# Note: Email is handled via SMTP (see .env for SMTP settings)
# Google Drive uses service account (service_account.json)

# Import State
from tiktok_slideshow_agent.state import AgentState

# Import Prompts
from tiktok_slideshow_agent.prompts.orchestrator import ORCHESTRATOR_INSTRUCTIONS
from tiktok_slideshow_agent.prompts.creative_director import CREATIVE_DIRECTOR_INSTRUCTIONS
from tiktok_slideshow_agent.prompts.specialists import (
    HOOK_AGENT_INSTRUCTIONS,
    STRATEGIST_INSTRUCTIONS,
    DESIGNER_INSTRUCTIONS,
    PUBLISHER_INSTRUCTIONS,
    QA_INSTRUCTIONS
)

# Import Tools
from tiktok_slideshow_agent.tools.agent_tools import (
    render_slide, 
    save_locally, 
    get_sync_tool, 
    setup_project_folder, 
    upload_to_drive, 
    send_email_notification,
    request_human_approval,
    read_format_library,
    search_pexels
)

# ==============================================================================
# Specialist 0: Creative Director (NEW - runs first)
# ==============================================================================
creative_director = {
    "name": "creative-director",
    "description": "Analyzes product/topic, selects optimal format from Format Library, creates Creative Brief that guides all downstream agents.",
    "system_prompt": CREATIVE_DIRECTOR_INSTRUCTIONS,
    "tools": [read_format_library, TavilySearch(max_results=3)],
}

# ==============================================================================
# Specialist 1: Hook Agent
# ==============================================================================
hook_agent = {
    "name": "hook-agent",
    "description": "Generates and selects the best hook for the slideshow following the Creative Brief.",
    "system_prompt": HOOK_AGENT_INSTRUCTIONS,
    "tools": [TavilySearch(max_results=3)], 
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

from tiktok_slideshow_agent.tools.vision_tool import verify_visual_consistency, select_best_fitting_image

# ==============================================================================
# Specialist 3: Visual Designer
# ==============================================================================
def get_visual_designer():
    # We'll use a placeholder and have the orchestrator or a middleware inject it,
    # or just accept that it's loaded when the subagent is initialized.
    # To avoid blocking at IMPORT time, we keep this as a function.
    
    return {
        "name": "visual-designer",
        "description": "Selects images suitables for the reel from content library.",
        "system_prompt": DESIGNER_INSTRUCTIONS, # Use raw instructions
        "tools": [get_sync_tool(), search_pexels, verify_visual_consistency, select_best_fitting_image], # render_slide moved to Publisher
    }


# ==============================================================================
# Specialist 4: Publisher
# ==============================================================================
def get_publisher():
    """Initialize publisher with Drive (service account) and SMTP email tools."""
    return {
        "name": "publisher",
        "description": "Sets up project, renders slides, uploads to Drive, and sends email notification.",
        "system_prompt": PUBLISHER_INSTRUCTIONS,
        "tools": [setup_project_folder, render_slide, save_locally, upload_to_drive, send_email_notification],
    }

# ==============================================================================
# Specialist 5: QA Specialist
# ==============================================================================
qa_specialist = {
    "name": "qa-specialist",
    "description": "Final quality control check.",
    "system_prompt": QA_INSTRUCTIONS,
    "tools": [request_human_approval], 
}

# ==============================================================================
# Model Configuration
# ==============================================================================
from tiktok_slideshow_agent.rotating_model import RotatingGeminiModel

def get_google_api_keys() -> list:
    """Get all available Google API keys from environment."""
    keys = []
    primary_key = os.getenv("GOOGLE_API_KEY")
    if primary_key:
        keys.append(primary_key)
    
    for i in range(2, 11): 
        key = os.getenv(f"GOOGLE_API_KEY_{i}")
        if key:
            keys.append(key)
    return keys

api_keys = get_google_api_keys()

# Use Gemini 2.5 Pro with Rotation support
model = RotatingGeminiModel(
    api_keys=api_keys,
    model="gemini-2.5-pro",
    temperature=0.7,
)


# ==============================================================================
# Create the Deep Agent
# ==============================================================================
from tiktok_slideshow_agent.state import AgentState
from deepagents.backends import CompositeBackend, StateBackend, FilesystemBackend

# Define the backend to route /image_library/ to the real disk
def get_backend(rt):
    # Calculate path relative to this file: .../tiktok_slideshow_agent/agent.py
    current_file = Path(__file__).resolve()
    image_library_path = current_file.parent / "image_library"
    
    return CompositeBackend(
        default=StateBackend(rt),
        routes={
            "/image_library/": FilesystemBackend(
                root_dir=str(image_library_path),
                virtual_mode=True
            ),
        }
    )

# Check for Human-in-the-Loop config - Defaulting to True for user visibility
enable_human_review = os.getenv("ENABLE_HUMAN_REVIEW", "True").lower() == "true"

# INTERRUPT CONFIGURATION
# We will handle interrupts DYNAMICALLY inside the 'request_human_approval' tool using langgraph.types.interrupt.
# So we do not need to configure static node interrupts here anymore.
interrupt_points = {}

agent = create_deep_agent(
    model=model,
    tools=[], # Orchestrator tools (if any)
    system_prompt=ORCHESTRATOR_INSTRUCTIONS,
    backend=get_backend,
    subagents=[
        creative_director,  # NEW: Runs first to create Creative Brief
        hook_agent,
        content_strategist,
        get_visual_designer(),
        qa_specialist,
        get_publisher()
    ],
    context_schema=AgentState,
    interrupt_on=interrupt_points,
)
