from jarvis_core.state import AgentState
from jarvis_core.agents.web_agent import WebAgent
from jarvis_core.agents.knowledge_agent import KnowledgeAgent
from jarvis_core.agents.system_agent import SystemAgent
from jarvis_core.agents.media_agent import MediaAgent

class Orchestrator:
    def __init__(self):
        self.state = AgentState()
        self.web_agent = WebAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.system_agent = SystemAgent()
        self.media_agent = MediaAgent()

    def route_command(self, command: str) -> str:
        """
        Routes the command to the appropriate agent based on keywords.
        """
        command_lower = command.lower()
        self.state.current_task = command
        
        # 1. System Control
        if any(word in command_lower for word in ["volume", "mute", "unmute", "open", "launch", "close", "type", "press"]):
            self.state.active_agent = "System"
            return self.system_agent.handle(command)
            
        # 2. Media Control
        elif any(word in command_lower for word in ["play", "song", "music", "video", "youtube"]):
            self.state.active_agent = "Media"
            return self.media_agent.play_song(command)
            
        # 3. Knowledge / Quick Answers (Replaced ResearchAgent)
        elif any(word in command_lower for word in ["who is", "what is", "tell me about", "how to", "find", "search", "define"]):
            self.state.active_agent = "Knowledge"
            return self.knowledge_agent.handle(command)
            
        # 4. General Web (Fallback)
        else:
            self.state.active_agent = "Web"
            return self.web_agent.handle(command)
