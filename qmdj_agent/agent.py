"""QMDJ Divination Agent - Main orchestrator with specialist sub-agents.

This module creates a conversational Qi Men Dun Jia divination agent that:
- Fetches real-time QMDJ charts
- Analyzes symbols through specialist agents
- Provides interactive, contextual readings
- Generates actionable strategic recommendations
"""

from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents import create_deep_agent

from qmdj_agent.prompts import (
    ORCHESTRATOR_INSTRUCTIONS,
    CHART_READER_INSTRUCTIONS,
    SYMBOL_INTERPRETER_INSTRUCTIONS,
    STRATEGY_ADVISOR_INSTRUCTIONS,
)
from qmdj_agent.tools import (
    qmdj_chart_api,
    symbol_lookup,
    element_interaction,
    calculate_score,
    think_tool,
)

# Configuration
max_concurrent_specialists = 3
max_consultation_rounds = 5

# Get current date for context
current_date = datetime.now().strftime("%Y-%m-%d")

# Specialist 1: Chart Reader
# Responsible for fetching and parsing QMDJ chart data
chart_reader = {
    "name": "chart-reader",
    "description": "Fetch and parse the Qi Men Dun Jia chart for the current time window. Use this to get raw chart data.",
    "system_prompt": CHART_READER_INSTRUCTIONS,
    "tools": [qmdj_chart_api, think_tool],
}

# Specialist 2: Symbol Interpreter
# Analyzes chart symbols in context of user's question
symbol_interpreter = {
    "name": "symbol-interpreter",
    "description": "Analyze QMDJ chart symbols in context of the user's question. Identifies positive/negative factors, conflicts, and ambiguities. Use this to interpret what the chart means.",
    "system_prompt": SYMBOL_INTERPRETER_INSTRUCTIONS,
    "tools": [symbol_lookup, element_interaction, calculate_score, think_tool],
}

# Specialist 3: Strategy Advisor
# Generates actionable recommendations based on chart analysis
strategy_advisor = {
    "name": "strategy-advisor",
    "description": "Generate specific, actionable strategic recommendations based on favorable palaces in the chart. Use this to provide practical guidance.",
    "system_prompt": STRATEGY_ADVISOR_INSTRUCTIONS,
    "tools": [think_tool, symbol_lookup],
}

# Model Configuration
# Using Gemini 2.0 Flash Thinking for enhanced reasoning
# You can switch to other models like Claude or GPT-4
model = ChatGoogleGenerativeAI(
    model="gemini-3-pro-preview",
    temperature=0.3  # Slightly creative for interpretations
)

# Create the QMDJ Divination Agent
agent = create_deep_agent(
    model=model,
    tools=[think_tool],  # Orchestrator only needs think_tool for reasoning
    system_prompt=ORCHESTRATOR_INSTRUCTIONS,
    subagents=[chart_reader, symbol_interpreter, strategy_advisor],
)
