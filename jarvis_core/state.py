from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class AgentState(BaseModel):
    """Shared state across all agents."""
    current_task: str = ""
    active_agent: str = "None"
    last_command: str = ""
    last_response: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)
