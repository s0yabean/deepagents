"""TikTok Slideshow Agent - Deep Agent Architecture."""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

# Import Deep Agent Factory
# Assuming deepagents is installed or available in path
try:
    from deepagents import create_deep_agent
except ImportError:
    # Fallback for dev environment if package not installed
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), "../qmdj_agent/.venv/lib/python3.12/site-packages"))
    from deepagents import create_deep_agent

# Import Prompts
from tiktok_slideshow_agent.prompts.orchestrator import ORCHESTRATOR_INSTRUCTIONS
from tiktok_slideshow_agent.prompts.specialists import (
    HOOK_AGENT_INSTRUCTIONS,
    STRATEGIST_INSTRUCTIONS,
    DESIGNER_INSTRUCTIONS,
    PUBLISHER_INSTRUCTIONS
)

# Import Tools
from tiktok_slideshow_agent.tools.agent_tools import search_images, render_slide, upload_and_save

# ==============================================================================
# Specialist 1: Hook Agent
# ==============================================================================
hook_agent = {
    "name": "hook-agent",
    "description": "Generates and selects the best hook for the slideshow.",
    "system_prompt": HOOK_AGENT_INSTRUCTIONS,
    "tools": [], # Pure LLM task, or maybe search_images if it needs inspiration
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
# Inject Image Library into Prompt
from tiktok_slideshow_agent.tools.agent_tools import image_lib
library_context = image_lib.get_all_images_as_text()
formatted_designer_prompt = DESIGNER_INSTRUCTIONS.format(image_library=library_context)

visual_designer = {
    "name": "visual-designer",
    "description": "Selects images and renders the final slides.",
    "system_prompt": formatted_designer_prompt,
    "tools": [render_slide], # search_images removed as library is in context
}

# ==============================================================================
# Specialist 4: Publisher
# ==============================================================================
publisher = {
    "name": "publisher",
    "description": "Uploads assets and logs the project.",
    "system_prompt": PUBLISHER_INSTRUCTIONS,
    "tools": [upload_and_save],
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
agent = create_deep_agent(
    model=model,
    tools=[], # Orchestrator tools (if any)
    system_prompt=ORCHESTRATOR_INSTRUCTIONS,
    subagents=[
        hook_agent,
        content_strategist,
        visual_designer,
        publisher
    ],
)
