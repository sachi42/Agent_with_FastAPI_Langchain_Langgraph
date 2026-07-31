# import operator
# from typing import TypedDict, Annotated, List, Dict, Any

# class AgentState(TypedDict):
#     messages: Annotated[List[Dict[str, Any]], operator.add]
#     session_id: str
#     tools_used: Annotated[List[str], operator.add]
#     sources: Annotated[List[str], operator.add]
#     iteration_count: int
#     tool_errors: int
#     final_response: str


# app/agent/state.py
import operator
from typing import TypedDict, Annotated, List, Dict, Any

def resetting_tracker_reducer(current: List[str], new_updates: List[str]) -> List[str]:
    """
    Production Reducer: Allows nodes to explicitly clear conversation-level 
    tool metrics by sending a '__RESET__' token on a new user query turn.
    """
    current_list = current or []
    new_list = new_updates or []
    
    # Check for the explicit systemic flush signal
    if new_list and new_list[0] == "__RESET__":
        # Return only the items following the reset token
        return new_list[1:]
        
    # Otherwise, maintain a unique combined chronological history for the active turn
    return list(dict.fromkeys(current_list + new_list))

class AgentState(TypedDict):
    messages: Annotated[List[Dict[str, Any]], operator.add] # Keeps conversation memory intact
    session_id: str
    iteration_count: int
    tool_errors: int
    final_response: str
    # Register our new resetting reducer to handle multi-turn isolation cleanly
    tools_used: Annotated[List[str], resetting_tracker_reducer]
    sources: Annotated[List[str], resetting_tracker_reducer]

