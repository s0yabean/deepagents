"""QMDJ Divination Agent - 8-Specialist Architecture.

This module creates a conversational Qi Men Dun Jia divination agent with:
- Chart Reader: Fetch real-time QMDJ charts
- Energy Analyzer: Calculate palace energy levels
- Symbol Interpreter: Analyze symbols with energy context
- Pattern Predictor: Identify converging patterns
- Probabilistic Agent: Monte Carlo simulations (NEW)
- Contrarian Agent: Devil's Advocate & Quality Control (NEW)
- QMDJ Strategy Advisor: Metaphysical recommendations
- Context Advisor: External evidence and grounding
"""

from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents import create_deep_agent

# Import Prompts from new modular structure
from qmdj_agent.prompts.orchestrator import ORCHESTRATOR_INSTRUCTIONS
from qmdj_agent.prompts.specialists import (
    CHART_READER_INSTRUCTIONS,
    ENERGY_ANALYZER_INSTRUCTIONS,
    SYMBOL_INTERPRETER_INSTRUCTIONS,
    PATTERN_PREDICTOR_INSTRUCTIONS,
    CONTEXT_ADVISOR_INSTRUCTIONS,
)
from qmdj_agent.prompts.qimen_advisor import STRATEGY_ADVISOR_INSTRUCTIONS
from qmdj_agent.prompts.analytical_agents import (
    PROBABILISTIC_SCENARIO_AGENT_INSTRUCTIONS,
    CONTRARIAN_AGENT_INSTRUCTIONS,
)
from qmdj_agent.prompts.packaging import PLAIN_SPEAKER_INSTRUCTIONS
from qmdj_agent.state import AgentState

# Import Tools from new modular structure
from qmdj_agent.tools.general import (
    get_current_time,
    tavily_search,
    reflect_on_reading,
)
from qmdj_agent.tools.sanitizer import sanitize_output
from qmdj_agent.tools.qimen import (
    qmdj_chart_api,
    calculate_box_energy,
    apply_tai_sui_modifier,
    detect_diagonal_overflow,
    symbol_lookup,
    five_element_interaction,
    calculate_score,
    compare_palaces,
    get_elemental_remedy,
)
from qmdj_agent.tools.simulation import run_monte_carlo_simulation

# Configuration
max_concurrent_specialists = 10
max_consultation_rounds = 10

# Get current date for context
current_date = datetime.now().strftime("%Y-%m-%d")

# ==============================================================================
# Specialist 1: Chart Reader
# ==============================================================================
chart_reader = {
    "name": "chart-reader",
    "description": "Fetch and parse the Qi Men Dun Jia chart for the current time window.",
    "system_prompt": CHART_READER_INSTRUCTIONS,
    "tools": [get_current_time, qmdj_chart_api, reflect_on_reading],
}

# ==============================================================================
# Specialist 2: Energy Analyzer
# ==============================================================================
energy_analyzer = {
    "name": "energy-analyzer",
    "description": "Calculate box energy levels based on Death/Emptiness, diagonal overflow, and Tai Sui effects.",
    "system_prompt": ENERGY_ANALYZER_INSTRUCTIONS,
    "tools": [get_current_time, calculate_box_energy, apply_tai_sui_modifier, detect_diagonal_overflow, reflect_on_reading],
}

# ==============================================================================
# Specialist 3: Symbol Interpreter
# ==============================================================================
symbol_interpreter = {
    "name": "symbol-interpreter",
    "description": "Analyze QMDJ symbols in context, considering energy levels. Identifies favorable/unfavorable factors.",
    "system_prompt": SYMBOL_INTERPRETER_INSTRUCTIONS,
    "tools": [get_current_time, symbol_lookup, five_element_interaction, calculate_score, calculate_box_energy, compare_palaces, reflect_on_reading],
}

# ==============================================================================
# Specialist 4: Pattern Predictor (Convergence Analysis)
# ==============================================================================
pattern_predictor = {
    "name": "pattern-predictor",
    "description": "Identify converging patterns across palaces to make specific, testable predictions. Creates the 'fortune teller effect'.",
    "system_prompt": PATTERN_PREDICTOR_INSTRUCTIONS,
    "tools": [get_current_time, reflect_on_reading],
}

# ==============================================================================
# Specialist 5: Probabilistic Scenario Agent (NEW)
# ==============================================================================
probabilistic_agent = {
    "name": "probabilistic-agent",
    "description": "Run Monte Carlo simulations to provide statistical probabilities for different outcomes based on the reading.",
    "system_prompt": PROBABILISTIC_SCENARIO_AGENT_INSTRUCTIONS,
    "tools": [run_monte_carlo_simulation, calculate_score, reflect_on_reading, tavily_search, get_current_time],
}

# ==============================================================================
# Specialist 6: Contrarian Agent (NEW)
# ==============================================================================
contrarian_agent = {
    "name": "contrarian-agent",
    "description": "Challenge assumptions, identify missing info, and mediate conflicts. Acts as Devil's Advocate.",
    "system_prompt": CONTRARIAN_AGENT_INSTRUCTIONS,
    "tools": [reflect_on_reading, tavily_search, get_current_time],
}

# ==============================================================================
# Specialist 7: QMDJ Strategy Advisor (Metaphysical)
# ==============================================================================
qmdj_strategy_advisor = {
    "name": "qmdj-advisor",
    "description": "Generate metaphysical strategic recommendations based on QMDJ principles. Uses calculate_score with energy weighting.",
    "system_prompt": STRATEGY_ADVISOR_INSTRUCTIONS,
    "tools": [get_current_time, calculate_score, symbol_lookup, five_element_interaction, calculate_box_energy, get_elemental_remedy, reflect_on_reading],
}

# ==============================================================================
# Specialist 8: Context Advisor (Evidence-Based)
# ==============================================================================
context_advisor = {
    "name": "context-advisor",
    "description": "Provide external evidence and real-world context to ground metaphysical insights. Searches for industry data, research, news.",
    "system_prompt": CONTEXT_ADVISOR_INSTRUCTIONS,
    "tools": [get_current_time, tavily_search, reflect_on_reading],
}

# ==============================================================================
# Specialist 9: Plain Speaker (Packaging Layer)
# ==============================================================================
plain_speaker = {
    "name": "plain-speaker",
    "description": "Reframe complex QMDJ analysis into plain English insights for the end user. Acts as a packaging layer.",
    "system_prompt": PLAIN_SPEAKER_INSTRUCTIONS,
    "tools": [reflect_on_reading],
}

# ==============================================================================
# Model Configuration
# ==============================================================================

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# Load environment variables
load_dotenv()

def get_google_api_keys() -> list:
    """Get all available Google API keys from environment.
    
    Checks for GOOGLE_API_KEY, GOOGLE_API_KEY_2, GOOGLE_API_KEY_3, etc.
    (Currently not used - switched to Claude)
    """
    keys = []
    # Check for primary key
    primary_key = os.getenv("GOOGLE_API_KEY")
    if primary_key:
        keys.append(primary_key)
    
    # Check for numbered backup keys
    for i in range(2, 10):  # Support up to GOOGLE_API_KEY_9
        key = os.getenv(f"GOOGLE_API_KEY_{i}")
        if key:
            keys.append(key)
    
    return keys

# Get all available API keys (for future use if switching back to Gemini)
api_keys = get_google_api_keys()

# Claude Sonnet 4.5 (commented out per user request)
# model = init_chat_model(
#     model="anthropic:claude-sonnet-4-5-20250929",
#     temperature=0.3
# )

from qmdj_agent.rotating_model import RotatingGeminiModel

# Google Gemini (Active - with Key Rotation)
model = RotatingGeminiModel(
    api_keys=api_keys,
    model="gemini-2.5-pro",
    #model="gemini-3-pro-preview", #seems to drastically reduce errors around wrong ClientResponses compared to flash.
    temperature=0.3
)

# ==============================================================================
# Create the QMDJ Divination Agent
# ==============================================================================
agent = create_deep_agent(
    model=model,
    tools=[get_current_time, reflect_on_reading, sanitize_output],
    system_prompt=ORCHESTRATOR_INSTRUCTIONS,
    subagents=[
        chart_reader,
        energy_analyzer,
        symbol_interpreter,
        pattern_predictor,
        probabilistic_agent,
        contrarian_agent,
        qmdj_strategy_advisor,
        context_advisor,
        plain_speaker,
    ],
    context_schema=AgentState,
)
