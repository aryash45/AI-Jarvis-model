"""
jarvis_core/orchestrator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
LangGraph-powered agent orchestrator.

Fix 3: imports RouterLLM (was OllamaManager / ollama_manager.py).
Fix 4: get_routing_decision() uses tool-calling to collapse the routing +
       query-contextualization into a single LLM call.
Fix 5: exposes stream_agent() and run_agent() so server.py can choose
       the streaming or non-streaming path per agent type.
Fix 6: route_command() is now backed by a LangGraph StateGraph with one
       node per agent and conditional edges from the router node.
"""

from typing import Any, Dict, Iterator, Optional
import logging

from langgraph.graph import StateGraph, START, END

from jarvis_core.state import AgentState
from jarvis_core.agents.web_agent import WebAgent
from jarvis_core.agents.knowledge_agent import KnowledgeAgent
from jarvis_core.agents.system_agent import SystemAgent
from jarvis_core.agents.media_agent import MediaAgent
from jarvis_core.router_llm import RouterLLM

logger = logging.getLogger(__name__)


# ── LangGraph state dict (plain dict, not Pydantic, as LangGraph requires) ───
# We keep AgentState (Pydantic) on self.state for the server.py interface, and
# use a plain TypedDict-style dict inside the graph.

GraphState = Dict[str, Any]


class Orchestrator:
    """
    One instance per WebSocket connection — per-connection isolation is
    preserved exactly as before; each Orchestrator has its own agent instances
    and its own compiled graph.
    """

    MAX_COMMAND_LENGTH = 500

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.state = AgentState()

        # ── Agent instances (per-connection, isolated history) ────────────────
        self.knowledge_agent = KnowledgeAgent(session_id=session_id)
        self.system_agent    = SystemAgent()
        self.media_agent     = MediaAgent()
        self.web_agent       = WebAgent()

        # ── RouterLLM (Fix 3: renamed from OllamaManager) ────────────────────
        self.router = RouterLLM()

        # ── Build LangGraph (Fix 6) ───────────────────────────────────────────
        self._graph = self._build_graph()
        logger.info("Orchestrator ready (session=%s)", session_id)

    # ── LangGraph construction ────────────────────────────────────────────────

    def _build_graph(self):
        """
        Compile a StateGraph with:
          START → router → [knowledge | media | system | web] → END
        """
        g = StateGraph(dict)

        # Nodes
        g.add_node("router",    self._node_router)
        g.add_node("knowledge", self._node_knowledge)
        g.add_node("media",     self._node_media)
        g.add_node("system",    self._node_system)
        g.add_node("web",       self._node_web)

        # Edges
        g.add_edge(START, "router")
        g.add_conditional_edges(
            "router",
            self._route_selector,
            {
                "KnowledgeAgent": "knowledge",
                "MediaAgent":     "media",
                "SystemAgent":    "system",
                "WebAgent":       "web",
            },
        )
        for node in ("knowledge", "media", "system", "web"):
            g.add_edge(node, END)

        return g.compile()

    # ── Graph nodes ───────────────────────────────────────────────────────────

    def _node_router(self, state: GraphState) -> GraphState:
        """Call RouterLLM and populate routing_decision + search_query_hint."""
        command = state["command"]
        routing = self.router.route_command(command)
        agent_name       = routing.get("agent", "KnowledgeAgent")
        search_hint      = routing.get("search_query_hint")
        state = dict(state)
        state["routing_decision"]  = agent_name
        state["search_query_hint"] = search_hint
        logger.info("Router → %s (hint=%s)", agent_name, search_hint)
        return state

    def _route_selector(self, state: GraphState) -> str:
        """Return the node name to branch to based on routing_decision."""
        decision = state.get("routing_decision", "KnowledgeAgent")
        # Normalise partial matches (e.g., "System" → "SystemAgent")
        for canonical in ("MediaAgent", "SystemAgent", "KnowledgeAgent", "WebAgent"):
            if canonical in decision or canonical.replace("Agent", "") in decision:
                return canonical
        return "KnowledgeAgent"

    def _node_knowledge(self, state: GraphState) -> GraphState:
        hint = state.get("search_query_hint")
        response = self.knowledge_agent.handle(state["command"], search_query_hint=hint)
        state = dict(state)
        state["response"] = response
        return state

    def _node_media(self, state: GraphState) -> GraphState:
        response = self.media_agent.play_song(state["command"])
        state = dict(state)
        state["response"] = response
        return state

    def _node_system(self, state: GraphState) -> GraphState:
        response = self.system_agent.handle(state["command"])
        state = dict(state)
        state["response"] = response
        return state

    def _node_web(self, state: GraphState) -> GraphState:
        response = self.web_agent.handle(state["command"])
        state = dict(state)
        state["response"] = response
        return state

    # ── Public API (server.py surface) ────────────────────────────────────────

    def get_routing_decision(self, command: str) -> Dict[str, Any]:
        """
        Fix 4+5: called by server.py before choosing the streaming vs
        non-streaming path. Returns the routing dict from RouterLLM without
        running the full agent yet.
        """
        command = self._validate_command(command)
        self.state.current_task = command
        routing = self.router.route_command(command)
        agent_name = routing.get("agent", "KnowledgeAgent")
        # Normalise
        for canonical in ("MediaAgent", "SystemAgent", "KnowledgeAgent", "WebAgent"):
            if canonical in agent_name or canonical.replace("Agent", "") in agent_name:
                agent_name = canonical
                break
        routing["agent"] = agent_name
        self.state.active_agent = agent_name
        return routing

    def stream_agent(self, command: str, routing_info: Dict[str, Any]) -> Iterator[str]:
        """
        Fix 5: stream text chunks from KnowledgeAgent / WebAgent.
        Called from server.py inside a thread-pool worker.
        """
        command = self._validate_command(command)
        agent_name = routing_info.get("agent", "KnowledgeAgent")
        hint       = routing_info.get("search_query_hint")

        if agent_name == "WebAgent":
            # WebAgent delegates to KnowledgeAgent
            ka = self.web_agent.knowledge_agent or self.knowledge_agent
            yield from ka.stream_handle(command, search_query_hint=hint)
        else:
            yield from self.knowledge_agent.stream_handle(command, search_query_hint=hint)

    def run_agent(self, command: str, routing_info: Dict[str, Any]) -> str:
        """
        Non-streaming path for MediaAgent / SystemAgent.
        Called from server.py inside a thread-pool worker.
        """
        command    = self._validate_command(command)
        agent_name = routing_info.get("agent", "SystemAgent")

        if agent_name == "MediaAgent":
            return self.media_agent.play_song(command)
        elif agent_name == "SystemAgent":
            return self.system_agent.handle(command)
        else:
            return self.knowledge_agent.handle(command)

    def route_command(self, command: str) -> str:
        """
        Backward-compatible blocking entry point (still works, but server.py
        now uses get_routing_decision + stream_agent / run_agent instead).

        Implemented via LangGraph graph.invoke() — Fix 6.
        """
        command = self._validate_command(command)
        if not command:
            return "Please provide a valid command."

        self.state.current_task = command
        try:
            result = self._graph.invoke({"command": command})
            agent_name = result.get("routing_decision", "None")
            # Normalise
            for canonical in ("MediaAgent", "SystemAgent", "KnowledgeAgent", "WebAgent"):
                if canonical in agent_name or canonical.replace("Agent", "") in agent_name:
                    agent_name = canonical
                    break
            self.state.active_agent = agent_name
            return result.get("response", "An error occurred.")
        except Exception as e:
            logger.error("Graph invocation error: %s", e, exc_info=True)
            return "An error occurred while processing your command. Please try again."

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _validate_command(self, command: str) -> str:
        if not command or not command.strip():
            return ""
        command = command.strip()
        if len(command) > self.MAX_COMMAND_LENGTH:
            logger.warning("Command truncated from %d chars", len(command))
            command = command[:self.MAX_COMMAND_LENGTH]
        return command
