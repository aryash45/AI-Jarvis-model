from jarvis_core.agents.knowledge_agent import KnowledgeAgent
import logging

class WebAgent:
    def __init__(self):
        # We delegate all web tasks to the KnowledgeAgent now so we don't open browser tabs.
        self.knowledge_agent = None

    def handle(self, command: str) -> str:
        """
        Unified handler for general web commands.
        We no longer redirect or open browser windows. We synthesize the answer directly.
        """
        if not self.knowledge_agent:
            self.knowledge_agent = KnowledgeAgent()
            
        logging.info("WebAgent received command, delegating to KnowledgeAgent for in-chat synthesis.")
        
        # Clean up command if it has explicit search keywords
        command_lower = command.lower()
        for phrase in ["search google for", "search for", "google", "wikipedia"]:
            if command_lower.startswith(phrase):
                command = command[len(phrase):].strip()
                break
                
        # Delegate to KnowledgeAgent to provide a verified, in-chat response
        return self.knowledge_agent.handle(command)
