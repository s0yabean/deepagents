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
    """Check the provided text for complex Qi Men Dun Jia jargon.
    
    This tool should be called on your almost-final response to the human.
    If any jargon terms are found, it will return a message identifying them
    and requesting a rephrase. If no jargon is found, it returns "success".
    
    Args:
        text: The draft response text to be checked for jargon.
    """
    found_terms = []
    
    # Check for each jargon term (case-insensitive)
    for term in JARGON_TERMS:
        # User wants full match for the term anywhere in the text, case-insensitive.
        # Removing word boundaries (\b) to catch substrings as well.
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        if pattern.search(text):
            found_terms.append(term)
    
    if found_terms:
        terms_str = ", ".join([f'"{t}"' for t in found_terms])
        return (
            f"Jargon detected: {terms_str}. "
            "Please remove these terms and rephrase your answer in simpler, "
            "layman-friendly consulting language before responding to the human."
        )
    
    return "success, no jargon detected."

@tool(parse_docstring=True)
def sanitize_agent_names(text: str) -> str:
    """Check the provided text for internal agent names that should not be exposed.
    
    This tool should be called on your almost-final response to the human, 
    in addition to the sanitize_output tool.
    
    Args:
        text: The draft response text to be checked for agent names.
    """
    found_names = []
    
    for name in AGENT_NAMES:
        # Case-insensitive substring match
        pattern = re.compile(re.escape(name), re.IGNORECASE)
        if pattern.search(text):
            found_names.append(name)
            
    if found_names:
        names_str = ", ".join([f'"{n}"' for n in found_names])
        return (
            f"Internal agent names detected: {names_str}. "
            "Please replace these specific agent names with phrases like 'Kiyun's agents', "
            "'our analysis', or 'the team' to accept the response."
        )
        
    return "success"
