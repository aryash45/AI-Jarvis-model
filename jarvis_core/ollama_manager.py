import os
import json
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Configure logging
logging.basicConfig(
    filename='logs/jarvis_security.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

FALLBACK_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
]

class OllamaManager:
    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        primary = os.getenv("OPENROUTER_MODEL", FALLBACK_MODELS[0])
        # Keep non-Gemma models at front since Gemma doesn't support system prompts
        non_gemma = [m for m in FALLBACK_MODELS if "gemma" not in m]
        gemma = [m for m in FALLBACK_MODELS if "gemma" in m]
        ordered = [primary] + [m for m in (non_gemma + gemma) if m != primary]
        self.models = ordered
        self.model_name = self.models[0]
        
        try:
            self._clients = [
                ChatOpenAI(
                    model=m,
                    openai_api_key=api_key,
                    openai_api_base="https://openrouter.ai/api/v1",
                    temperature=0.1,
                    max_retries=0,
                )
                for m in self.models
            ]
            self.llm = self._clients[0]
            self.enabled = True
            logging.info(f"OpenRouter AI initialized with {len(self._clients)} models, primary: {self.model_name}")
        except Exception as e:
            logging.warning(f"Failed to initialize OpenRouter: {str(e)}")
            self.enabled = False
            
    def _call_llm(self, messages):
        """Try each model in order, falling back on 429/400 errors."""
        last_error = None
        for i, client in enumerate(self._clients):
            try:
                result = client.invoke(messages)
                if i > 0:
                    logging.info(f"Router fallback succeeded with: {self.models[i]}")
                return result
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "400" in err_str or "rate" in err_str.lower():
                    logging.warning(f"Router model {self.models[i]} failed ({err_str[:80]}), trying next...")
                    last_error = e
                    continue
                raise
        raise last_error

    def route_command(self, command: str) -> Dict[str, Any]:
        """
        Use AI to determine which agent should handle the command.
        Returns: {"agent": "AgentName", "confidence": 0.9}
        """
        if not self.enabled or not os.getenv("OPENROUTER_API_KEY"):
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
            response = self._call_llm([
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
            return "AI is not configured. Please set OPENROUTER_API_KEY."
            
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        try:
            response = self._call_llm(messages)
            return response.content
        except Exception as e:
            logging.error(f"OpenRouter chat failed: {str(e)}")
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
