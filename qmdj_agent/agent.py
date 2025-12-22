"""QMDJ Divination Agent - 5-Specialist Architecture.

This module creates a conversational Qi Men Dun Jia divination agent with:
- Chart Reader: Fetch real-time QMDJ charts
- Energy Analyzer: Calculate palace energy levels
- Symbol Interpreter: Analyze symbols with energy context
- QMDJ Strategy Advisor: Metaphysical recommendations
- Context Advisor: External evidence and grounding
"""

from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents import create_deep_agent

from qmdj_agent.prompts import (
    ORCHESTRATOR_INSTRUCTIONS,
    CHART_READER_INSTRUCTIONS,
    ENERGY_ANALYZER_INSTRUCTIONS,
    SYMBOL_INTERPRETER_INSTRUCTIONS,
    PATTERN_PREDICTOR_INSTRUCTIONS,
    STRATEGY_ADVISOR_INSTRUCTIONS,
    CONTEXT_ADVISOR_INSTRUCTIONS,
)
from qmdj_agent.tools import (
    get_current_time,
    qmdj_chart_api,
    calculate_box_energy,
    apply_tai_sui_modifier,
    detect_diagonal_overflow,
    symbol_lookup,
    five_element_interaction,
    calculate_score,
    tavily_search,
    reflect_on_reading,
)

# Configuration
max_concurrent_specialists = 6
max_consultation_rounds = 5

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
# Specialist 2: Energy Analyzer (NEW)
# ==============================================================================
energy_analyzer = {
    "name": "energy-analyzer",
    "description": "Calculate box energy levels based on Death/Emptiness, diagonal overflow, and Tai Sui effects.",
    "system_prompt": ENERGY_ANALYZER_INSTRUCTIONS,
    "tools": [calculate_box_energy, apply_tai_sui_modifier, detect_diagonal_overflow, reflect_on_reading],
}

# ==============================================================================
# Specialist 3: Symbol Interpreter
# ==============================================================================
symbol_interpreter = {
    "name": "symbol-interpreter",
    "description": "Analyze QMDJ symbols in context, considering energy levels. Identifies favorable/unfavorable factors.",
    "system_prompt": SYMBOL_INTERPRETER_INSTRUCTIONS,
    "tools": [symbol_lookup, five_element_interaction, reflect_on_reading],
}

# ==============================================================================
# Specialist 4: Pattern Predictor (Convergence Analysis) (NEW)
# ==============================================================================
pattern_predictor = {
    "name": "pattern-predictor",
    "description": "Identify converging patterns across palaces to make specific, testable predictions. Creates the 'fortune teller effect'.",
    "system_prompt": PATTERN_PREDICTOR_INSTRUCTIONS,
    "tools": [reflect_on_reading],
}

# ==============================================================================
# Specialist 5: QMDJ Strategy Advisor (Metaphysical)
# ==============================================================================
qmdj_strategy_advisor = {
    "name": "qmdj-advisor",
    "description": "Generate metaphysical strategic recommendations based on QMDJ principles. Uses calculate_score with energy weighting.",
    "system_prompt": STRATEGY_ADVISOR_INSTRUCTIONS,
    "tools": [calculate_score, symbol_lookup, reflect_on_reading],
}

# ==============================================================================
# Specialist 6: Context Advisor (Evidence-Based)
# ==============================================================================
context_advisor = {
    "name": "context-advisor",
    "description": "Provide external evidence and real-world context to ground metaphysical insights. Searches for industry data, research, news.",
    "system_prompt": CONTEXT_ADVISOR_INSTRUCTIONS,
    "tools": [tavily_search, reflect_on_reading],
}

# ==============================================================================
# Model Configuration
# ==============================================================================
model = ChatGoogleGenerativeAI(
    model="gemini-3-pro-preview",
    temperature=0.3  # Slightly creative for interpretations
)

# ==============================================================================
# Create the QMDJ Divination Agent
# ==============================================================================
agent = create_deep_agent(
    model=model,
    tools=[reflect_on_reading],
    system_prompt=ORCHESTRATOR_INSTRUCTIONS,
    subagents=[
        chart_reader,
        energy_analyzer,
        symbol_interpreter,
        pattern_predictor,
        qmdj_strategy_advisor,
        context_advisor,
    ],
)
