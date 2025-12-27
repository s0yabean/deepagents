from typing import Annotated, List, TypedDict, Optional, Any, NotRequired, Dict
import operator

class AgentState(TypedDict):
    """State schema for the QMDJ agent."""
    
    # QMDJ Specific Context
    chart_json: NotRequired[str]
    energy_json: NotRequired[str]
    current_question: NotRequired[str]
    
    # Analysis results
    specialist_findings: NotRequired[List[Dict[str, Any]]]
    final_reading: NotRequired[str]
    
    # Planning (Explicitly defined to handle concurrent updates)
    # Use a reducer that keeps the last update (y) to prevent InvalidUpdateError
    todos: Annotated[List[Dict[str, Any]], lambda x, y: y]
