import os
import json
import logging
from typing import Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

# Configure logging
logging.basicConfig(
    filename='logs/jarvis_security.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class OllamaManager:
    def __init__(self):
        # Determine ollama host (if any, defaults to localhost:11434)
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3")
        
        try:
            self.llm = ChatOllama(model=self.model_name, base_url=ollama_host, temperature=0.1)
            self.enabled = True
            logging.info(f"Ollama AI initialized successfully with model {self.model_name}")
        except Exception as e:
            logging.warning(f"Failed to initialize Ollama: {str(e)}")
            self.enabled = False
            
    def route_command(self, command: str) -> Dict[str, Any]:
        """
        Use AI to determine which agent should handle the command.
        Returns: {"agent": "AgentName", "confidence": 0.9}
        """
        if not self.enabled:
            return self._keyword_fallback(command)
            
        system_prompt = """You are a routing assistant for Jarvis, an AI assistant.

Available agents:
- MediaAgent: Play music/videos on YouTube (e.g., "play shape of you", "play rock music")
- SystemAgent: Control volume, open apps/system tools (e.g., "mute volume", "open notepad")
- KnowledgeAgent: ALL other queries, including general conversation, greetings, questions, and web searches (e.g., "hello", "how are you", "who is Elon Musk")

Analyze the command and respond with ONLY a JSON object (no markdown, no explanation):
{"agent": "AgentName", "confidence": 0.95}

Example responses:
{"agent": "MediaAgent", "confidence": 0.9}
{"agent": "SystemAgent", "confidence": 0.85}
{"agent": "KnowledgeAgent", "confidence": 0.99}
"""
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f'User command: "{command}"')
            ])
            
            content = response.content.strip()
            
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
                
            result = json.loads(content)
            logging.info(f"AI routed command to {result.get('agent')} with confidence {result.get('confidence')}")
            return result
        except Exception as e:
            logging.error(f"Ollama AI routing failed: {str(e)}")
            return self._keyword_fallback(command)
            
    def chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.enabled:
            return "AI is not configured. Please check Ollama setup."
            
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        try:
            # We use a higher temp for general chat if needed, but we'll stick to default configured.
            chat_llm = ChatOllama(model=self.model_name, temperature=0.7)
            response = chat_llm.invoke(messages)
            return response.content
        except Exception as e:
            logging.error(f"Ollama chat failed: {str(e)}")
            return f"AI Error: {str(e)}"
            
    def _keyword_fallback(self, command: str) -> Dict[str, Any]:
        """Simple keyword-based routing when AI is unavailable"""
        cmd_lower = command.lower()
        if any(word in cmd_lower for word in ["play", "music", "song", "video", "youtube"]):
            return {"agent": "MediaAgent", "confidence": 0.7}
        elif any(word in cmd_lower for word in ["volume", "mute", "unmute", "open", "launch"]):
            return {"agent": "SystemAgent", "confidence": 0.7}
        else:
            # Default everything else to KnowledgeAgent for ChatGPT-like experience
            return {"agent": "KnowledgeAgent", "confidence": 0.9}
