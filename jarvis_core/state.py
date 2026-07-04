from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class AgentState(BaseModel):
    """Shared state across all agents (also used as LangGraph graph state)."""
    current_task: str = ""
    active_agent: str = "None"
    last_command: str = ""
    last_response: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)

    # Fix 6: routing fields used by the LangGraph graph
    routing_decision: str = ""
    search_query_hint: Optional[str] = None
