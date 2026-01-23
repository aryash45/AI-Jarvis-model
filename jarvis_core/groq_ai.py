import os
import json
import logging
from typing import Dict, Any, Optional
from groq import Groq

# Configure logging
logging.basicConfig(
    filename='logs/jarvis_security.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class GroqAI:
    
    
    def __init__(self):
        # Get API key from environment variable
        self.api_key = os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            logging.warning("GROQ_API_KEY not found. AI routing disabled.")
            self.enabled = False
        else:
            self.client = Groq(api_key=self.api_key)
            self.enabled = True
            logging.info("Groq AI initialized successfully")
        
        # Use Llama 3.1 8B - fast and smart
        self.model = "llama-3.1-8b-instant"
    
    def route_command(self, command: str) -> Dict[str, Any]:
        """
        Use AI to determine which agent should handle the command.
        Returns: {"agent": "AgentName", "action": "action", "params": {...}}
        """
        
        if not self.enabled:
            # Fallback to simple keyword matching
            return self._keyword_fallback(command)
        
        prompt = f"""You are a routing assistant for Jarvis, an AI assistant.

Available agents:
- MediaAgent: Play music/videos on YouTube (e.g., "play shape of you", "play rock music")
- SystemAgent: Control volume, open apps (e.g., "mute volume", "open notepad")
- KnowledgeAgent: Answer questions, search Wikipedia (e.g., "who is Einstein", "what is Python")
- WebAgent: General web search (fallback for everything else)

User command: "{command}"

Analyze the command and respond with ONLY a JSON object (no markdown, no explanation):
{{"agent": "AgentName", "confidence": 0.95}}

Example responses:
{{"agent": "MediaAgent", "confidence": 0.9}}
{{"agent": "SystemAgent", "confidence": 0.85}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent routing
                max_tokens=100
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            result = json.loads(content)
            
            logging.info(f"AI routed command to {result.get('agent')} with confidence {result.get('confidence')}")
            return result
            
        except Exception as e:
            logging.error(f"Groq AI routing failed: {str(e)}")
            # Fallback to keyword matching
            return self._keyword_fallback(command)
    
    def chat(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 500) -> str:
        """
        General chat completion for any AI task.
        Use this for code explanation, error debugging, etc.
        """
        
        if not self.enabled:
            return "AI is not configured. Please set GROQ_API_KEY environment variable."
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Groq chat failed: {str(e)}")
            return f"AI Error: {str(e)}"
    
    def _keyword_fallback(self, command: str) -> Dict[str, Any]:
        """Simple keyword-based routing when AI is unavailable"""
        cmd_lower = command.lower()
        
        if any(word in cmd_lower for word in ["play", "music", "song", "video", "youtube"]):
            return {"agent": "MediaAgent", "confidence": 0.7}
        
        elif any(word in cmd_lower for word in ["volume", "mute", "unmute", "open", "launch"]):
            return {"agent": "SystemAgent", "confidence": 0.7}
        
        elif any(word in cmd_lower for word in ["who is", "what is", "tell me", "define", "search"]):
            return {"agent": "KnowledgeAgent", "confidence": 0.7}
        
        else:
            return {"agent": "WebAgent", "confidence": 0.5}


# Example usage and testing
if __name__ == "__main__":
    # Test the AI router
    ai = GroqAI()
    
    test_commands = [
        "play some jazz music",
        "open calculator",
        "who is Albert Einstein",
        "search for Python tutorials"
    ]
    
    for cmd in test_commands:
        result = ai.route_command(cmd)
        print(f"Command: {cmd}")
        print(f"Route: {result}")
        print()
