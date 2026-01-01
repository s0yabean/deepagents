"""Tool for sanitizing agent output to remove complex QMDJ jargon."""

from langchain_core.tools import tool
import re

# List of terms to avoid in final responses
JARGON_TERMS = [
    "QMDJ", 
    "Qi Men Dun Jia", 
    "QiMenDunJia",
    "Qimen", 
    "Gan Zhi", 
    "Fu Yin", 
    "Fan Yin", 
    "Zhi Fu", 
    "Zhi Shi", 
    "Death/Emptiness", 
    "Tai Sui", 
    "Metal chops Wood",
    "Empty Palace",
    "Death Palace",
    "Nine Stars",
    "Eight Doors",
    "Eight Gods",
    "Ten Gan",
    "Twelve Zhi"
]

# List of internal agent names to avoid exposing
AGENT_NAMES = [
    "chart-reader",
    "energy-analyzer",
    "symbol-interpreter",
    "pattern-predictor",
    "probabilistic-agent",
    "contrarian-agent",
    "qmdj-advisor",
    "context-advisor",
    "plain-speaker"
]

@tool(parse_docstring=True)
def sanitize_output(text: str) -> str:
    """Check the provided text for BOTH complex QMDJ jargon AND internal agent names.
    
    This tool acts as a single gatekeeper. It ensures the response is:
    1. Free of forbidden QMDJ technical terms (unless explained simply).
    2. Free of internal agent names (e.g., 'chart-reader').
    
    Args:
        text: The draft response text to be checked.
    """
    feedback = []
    
    # Check 1: Jargon Terms
    found_jargon = []
    for term in JARGON_TERMS:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        if pattern.search(text):
            found_jargon.append(term)
            
    if found_jargon:
        jargon_str = ", ".join([f'"{t}"' for t in found_jargon])
        feedback.append(
            f"Jargon detected: {jargon_str}. Remove or rephrase into plain English."
        )

    # Check 2: Agent Names
    found_names = []
    for name in AGENT_NAMES:
        pattern = re.compile(re.escape(name), re.IGNORECASE)
        if pattern.search(text):
            found_names.append(name)
            
    if found_names:
        names_str = ", ".join([f'"{n}"' for n in found_names])
        feedback.append(
            f"Internal agent names detected: {names_str}. Replace with phrases like 'Kiyun's agents' or 'our analysis'."
        )
    
    # Return consolidated feedback
    if feedback:
        return "Sanitization Failed:\n" + "\n".join(feedback)
    
    return "success, no jargon or agent names detected."
