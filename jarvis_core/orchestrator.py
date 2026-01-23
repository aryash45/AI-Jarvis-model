from jarvis_core.state import AgentState
from jarvis_core.agents.web_agent import WebAgent
from jarvis_core.agents.knowledge_agent import KnowledgeAgent
from jarvis_core.agents.system_agent import SystemAgent
from jarvis_core.agents.media_agent import MediaAgent
from jarvis_core.groq_ai import GroqAI
import logging

# Configure logging
logging.basicConfig(
    filename='logs/jarvis_security.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Orchestrator:
    MAX_COMMAND_LENGTH = 500
    
    def __init__(self):
        self.state = AgentState()
        self.web_agent = WebAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.system_agent = SystemAgent()
        self.media_agent = MediaAgent()
        
        # NEW: AI-powered routing with Groq
        self.ai = GroqAI()
        logging.info("Orchestrator initialized with Groq AI routing")

    def route_command(self, command: str) -> str:
        """
        Routes the command to the appropriate agent using AI.
        Falls back to keyword matching if AI is unavailable.
        """
        try:
            # Input validation
            if not command or not command.strip():
                return "Please provide a valid command."
            
            command = command.strip()
            
            # Length validation
            if len(command) > self.MAX_COMMAND_LENGTH:
                logging.warning(f"Command exceeded max length: {len(command)} chars")
                command = command[:self.MAX_COMMAND_LENGTH]
            
            self.state.current_task = command
            
            logging.info(f"Processing command: {command[:100]}")
            
            # Use AI to determine which agent to route to
            routing = self.ai.route_command(command)
            
            # Handle both dictionary formats
            if isinstance(routing, dict):
                # Check if 'agent' key exists directly
                if 'agent' in routing:
                    agent_name = routing['agent']
                    confidence = routing.get('confidence', 'N/A')
                else:
                    # Fallback - might be nested or malformed
                    agent_name = routing.get('agent', 'WebAgent')
                    confidence = 'N/A'
            else:
                # Unexpected format
                agent_name = 'WebAgent'
                confidence = 'N/A'
            
            self.state.active_agent = agent_name
            logging.info(f"AI routed to {agent_name} (confidence: {confidence})")
            
            # Route to the appropriate agent based on name
            if agent_name == "SystemAgent" or "System" in agent_name:
                return self.system_agent.handle(command)
            
            elif agent_name == "MediaAgent" or "Media" in agent_name:
                return self.media_agent.play_song(command)
            
            elif agent_name == "KnowledgeAgent" or "Knowledge" in agent_name:
                return self.knowledge_agent.handle(command)
            
            elif agent_name == "WebAgent" or "Web" in agent_name:
                return self.web_agent.handle(command)
            
            else:
                # Unknown agent, default to web
                logging.warning(f"Unknown agent: {agent_name}, defaulting to WebAgent")
                return self.web_agent.handle(command)
                
        except Exception as e:
            logging.error(f"Error in route_command: {str(e)}")
            return f"An error occurred while processing your command. Please try again."
