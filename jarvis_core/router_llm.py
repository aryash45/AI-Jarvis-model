"""
jarvis_core/router_llm.py
~~~~~~~~~~~~~~~~~~~~~~~~~
OpenRouter API client used for agent routing and chat.

Renamed from ollama_manager.py / OllamaManager — this class never touched
Ollama or any local model; the accurate name is RouterLLM.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

FALLBACK_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
]

# Agents available for routing — used both in the prompt and in tool schema
AGENT_NAMES = ["MediaAgent", "SystemAgent", "KnowledgeAgent"]

# OpenAI-style tool schema for structured routing
_ROUTING_TOOL = {
    "type": "function",
    "function": {
        "name": "route_to_agent",
        "description": "Route the user command to the appropriate Jarvis agent.",
        "parameters": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "enum": AGENT_NAMES,
                    "description": "The agent best suited to handle this command.",
                },
                "confidence": {
                    "type": "number",
                    "description": "Routing confidence 0–1.",
                },
                "search_query_hint": {
                    "type": "string",
                    "description": (
                        "Optional: a reformulated, standalone web-search query for "
                        "KnowledgeAgent (omit for other agents)."
                    ),
                },
            },
            "required": ["agent", "confidence"],
        },
    },
}

_ROUTING_SYSTEM = """\
You are a routing assistant for Jarvis, an AI assistant.

Available agents:
- MediaAgent: Play music/videos on YouTube (e.g., "play shape of you", "play rock music")
- SystemAgent: Control volume, open apps/system tools (e.g., "mute volume", "open notepad")
- KnowledgeAgent: ALL other queries, including general conversation, greetings, questions, \
and web searches (e.g., "hello", "how are you", "who is Elon Musk")

Call the `route_to_agent` function with the correct agent name and a confidence score.
"""


class RouterLLM:
    """
    OpenRouter API client for agent routing and fallback chat.

    Tries each model in *FALLBACK_MODELS* order on 429/400 errors.
    Uses OpenAI-style tool/function calling for structured routing where
    the model supports it; falls back to JSON-prompt routing otherwise.
    """

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        primary = os.getenv("OPENROUTER_MODEL", FALLBACK_MODELS[0])
        # Keep non-Gemma models at front: Gemma doesn't support system prompts
        non_gemma = [m for m in FALLBACK_MODELS if "gemma" not in m]
        gemma = [m for m in FALLBACK_MODELS if "gemma" in m]
        ordered = [primary] + [m for m in (non_gemma + gemma) if m != primary]
        self.models = ordered
        self.model_name = self.models[0]

        try:
            self._clients: List[ChatOpenAI] = [
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
            logger.info(
                "RouterLLM initialized with %d models, primary: %s",
                len(self._clients),
                self.model_name,
            )
        except Exception as e:
            logger.warning("Failed to initialize RouterLLM: %s", e)
            self.enabled = False

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _call_llm(self, messages, **kwargs):
        """Try each model in order, falling back on 429/400 errors."""
        last_error = None
        for i, client in enumerate(self._clients):
            try:
                result = client.invoke(messages, **kwargs)
                if i > 0:
                    logger.info("RouterLLM fallback succeeded with: %s", self.models[i])
                return result
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "400" in err_str or "rate" in err_str.lower():
                    logger.warning(
                        "RouterLLM model %s failed (%s…), trying next",
                        self.models[i],
                        err_str[:80],
                    )
                    last_error = e
                    continue
                raise
        raise last_error or RuntimeError("RouterLLM: all models exhausted with no error captured")

    # ── Public API ────────────────────────────────────────────────────────────

    def route_command(self, command: str) -> Dict[str, Any]:
        """
        Determine which agent should handle *command*.

        Tries tool-calling first (single structured call), falls back to a
        JSON-prompt approach, then to keyword matching.

        Returns: {"agent": "AgentName", "confidence": float,
                  "search_query_hint": str | None}
        """
        if not self.enabled or not os.getenv("OPENROUTER_API_KEY"):
            return self._keyword_fallback(command)

        # ── Attempt 1: tool/function calling (one round-trip) ─────────────
        try:
            result = self._route_with_tools(command)
            if result:
                return result
        except Exception as e:
            logger.warning("Tool-call routing failed (%s), trying JSON fallback", e)

        # ── Attempt 2: JSON-prompt fallback ───────────────────────────────
        try:
            return self._route_with_json_prompt(command)
        except Exception as e:
            logger.error("JSON routing failed: %s", e)
            return self._keyword_fallback(command)

    def _route_with_tools(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Single LLM call using OpenAI tool calling.
        Returns the parsed routing dict or None on failure.
        """
        messages = [
            SystemMessage(content=_ROUTING_SYSTEM),
            HumanMessage(content=f'User command: "{command}"'),
        ]
        response = self._call_llm(messages, tools=[_ROUTING_TOOL], tool_choice="auto")

        # Extract tool-call arguments
        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            # Some models put it in additional_kwargs
            raw = response.additional_kwargs.get("tool_calls", [])
            if raw:
                tool_calls = raw

        if not tool_calls:
            return None  # Model didn't call the tool; fall through to JSON prompt

        tc = tool_calls[0]
        # LangChain wraps args as a dict; raw OpenAI wraps as JSON string
        if isinstance(tc, dict):
            args_raw = tc.get("function", {}).get("arguments", "{}")
            args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
        else:
            # LangChain ToolCall object
            args = tc.args if hasattr(tc, "args") else {}

        agent = args.get("agent", "KnowledgeAgent")
        result = {
            "agent": agent,
            "confidence": float(args.get("confidence", 0.9)),
            "search_query_hint": args.get("search_query_hint"),
        }
        logger.info(
            "RouterLLM tool-call routed to %s (conf=%.2f)",
            result["agent"],
            result["confidence"],
        )
        return result

    def _route_with_json_prompt(self, command: str) -> Dict[str, Any]:
        """
        Legacy JSON-prompt routing — kept as fallback for models that don't
        support tool calling (e.g., free Gemma models on OpenRouter).
        """
        system_prompt = """\
You are a routing assistant for Jarvis, an AI assistant.

Available agents:
- MediaAgent: Play music/videos on YouTube
- SystemAgent: Control volume, open apps/system tools
- KnowledgeAgent: ALL other queries

Respond with ONLY a JSON object (no markdown):
{"agent": "AgentName", "confidence": 0.95}"""

        response = self._call_llm([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f'User command: "{command}"'),
        ])

        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)
        data.setdefault("search_query_hint", None)
        logger.info(
            "RouterLLM JSON-prompt routed to %s (conf=%s)",
            data.get("agent"),
            data.get("confidence"),
        )
        return data

    def chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Simple chat helper used outside of routing."""
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
            logger.error("RouterLLM chat failed: %s", e)
            return f"AI Error: {e}"

    def _keyword_fallback(self, command: str) -> Dict[str, Any]:
        """Simple keyword-based routing when AI is unavailable."""
        cmd_lower = command.lower()
        if any(w in cmd_lower for w in ["play", "music", "song", "video", "youtube"]):
            return {"agent": "MediaAgent", "confidence": 0.7, "search_query_hint": None}
        if any(w in cmd_lower for w in ["volume", "mute", "unmute", "open", "launch"]):
            return {"agent": "SystemAgent", "confidence": 0.7, "search_query_hint": None}
        return {"agent": "KnowledgeAgent", "confidence": 0.9, "search_query_hint": None}
