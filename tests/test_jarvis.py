"""
tests/test_jarvis.py
~~~~~~~~~~~~~~~~~~~~
Real pytest test suite with assertions and mocked LLM/network calls.

Fix 8: replaces the old print-only test_agents() with:
  - Proper assertions on return values and routing state
  - unittest.mock patches so no live API keys / network calls are needed
  - pytest.mark.skipif guards for environments without API keys

Run with:
    python -m pytest tests/ -v
"""

import os
import pytest
from unittest.mock import patch, MagicMock, PropertyMock


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fake_ai_message(text: str):
    """Return a mock LangChain AIMessage-like object."""
    msg = MagicMock()
    msg.content = text
    msg.tool_calls = []
    msg.additional_kwargs = {}
    return msg


def _fake_stream(text: str):
    """Return an iterator of mock chunk objects, one word per chunk."""
    for word in text.split():
        yield _fake_ai_message(word + " ")


# ── Fix 8: keyword-fallback routing (no API key required) ────────────────────

@pytest.fixture()
def router_llm(monkeypatch):
    """RouterLLM instance with ChatOpenAI patched out — no network."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    with patch("jarvis_core.router_llm.ChatOpenAI"):
        from jarvis_core.router_llm import RouterLLM
        r = RouterLLM()
        r.enabled = True  # force enabled even without real key
        return r


class TestKeywordFallback:
    """RouterLLM._keyword_fallback() — pure Python, no network."""

    def test_play_routes_to_media(self, router_llm):
        assert router_llm._keyword_fallback("play shape of you")["agent"] == "MediaAgent"

    def test_mute_routes_to_system(self, router_llm):
        assert router_llm._keyword_fallback("mute volume")["agent"] == "SystemAgent"

    def test_question_routes_to_knowledge(self, router_llm):
        assert router_llm._keyword_fallback("who is Albert Einstein")["agent"] == "KnowledgeAgent"

    def test_fallback_has_confidence(self, router_llm):
        result = router_llm._keyword_fallback("hello")
        assert "confidence" in result
        assert 0 < result["confidence"] <= 1.0

    def test_open_routes_to_system(self, router_llm):
        assert router_llm._keyword_fallback("open notepad")["agent"] == "SystemAgent"

    def test_generic_query_defaults_to_knowledge(self, router_llm):
        assert router_llm._keyword_fallback("what is Python")["agent"] == "KnowledgeAgent"


# ── Fix 8: KnowledgeAgent unit tests ─────────────────────────────────────────

@pytest.fixture()
def knowledge_agent(monkeypatch):
    """KnowledgeAgent with all external calls mocked."""
    with (
        patch("jarvis_core.agents.knowledge_agent.ChatOpenAI"),
        patch("jarvis_core.agents.knowledge_agent.DuckDuckGoSearchRun"),
        patch("jarvis_core.memory.load_history", return_value=[]),
        patch("jarvis_core.memory.append_turn"),
        patch("jarvis_core.agents.knowledge_agent.BrowserTools"),
    ):
        from jarvis_core.agents.knowledge_agent import KnowledgeAgent
        agent = KnowledgeAgent(session_id="test-session")

    # Inject a working mock LLM client after init
    mock_client = MagicMock()
    mock_client.invoke.return_value = _fake_ai_message("Albert Einstein was a physicist.")
    mock_client.stream.return_value = _fake_stream("Albert Einstein was a famous physicist.")

    agent._llm_clients = [mock_client]
    agent.model_names  = ["mock-model"]
    agent.enabled      = True
    agent.web_search   = MagicMock(run=MagicMock(return_value=""))

    # Patch append_turn so we don't hit real DB
    with patch("jarvis_core.memory.append_turn"):
        yield agent, mock_client


class TestKnowledgeAgent:
    """KnowledgeAgent.handle() and stream_handle() — fully mocked."""

    def test_handle_returns_nonempty_string(self, knowledge_agent):
        agent, _ = knowledge_agent
        with patch("jarvis_core.memory.append_turn"):
            result = agent.handle("who is Albert Einstein")
        assert isinstance(result, str)
        assert len(result.strip()) > 0

    def test_stream_handle_yields_chunks(self, knowledge_agent):
        agent, mock_client = knowledge_agent
        mock_client.stream.return_value = _fake_stream("This is the answer.")
        with patch("jarvis_core.memory.append_turn"):
            chunks = list(agent.stream_handle("who is Albert Einstein"))
        assert len(chunks) > 0
        assert len("".join(chunks).strip()) > 0

    def test_greeting_skips_web_search(self, knowledge_agent):
        """Casual greeting should NOT call web_search.run()."""
        agent, mock_client = knowledge_agent
        mock_client.stream.return_value = _fake_stream("Hello there!")
        with patch("jarvis_core.memory.append_turn"):
            list(agent.stream_handle("hello"))
        agent.web_search.run.assert_not_called()

    def test_empty_history_skips_contextualization(self, knowledge_agent):
        """Empty history → invoke() not called for query rewriting (only stream)."""
        agent, mock_client = knowledge_agent
        agent.history = []
        mock_client.stream.return_value = _fake_stream("The answer is 42.")
        mock_client.invoke.reset_mock()
        with patch("jarvis_core.memory.append_turn"):
            list(agent.stream_handle("what is the answer to everything"))
        # invoke should NOT have been called (only stream() for the final answer)
        mock_client.invoke.assert_not_called()

    def test_search_query_hint_skips_invoke(self, knowledge_agent):
        """When a search_query_hint is provided, no extra invoke() call needed."""
        agent, mock_client = knowledge_agent
        agent.history = [{"role": "User", "content": "tell me about it"}]
        mock_client.stream.return_value = _fake_stream("Sure, here is info.")
        mock_client.invoke.reset_mock()
        with patch("jarvis_core.memory.append_turn"):
            list(agent.stream_handle("what about the war", search_query_hint="World War II overview"))
        mock_client.invoke.assert_not_called()


# ── Fix 8: Orchestrator routing ───────────────────────────────────────────────

@pytest.fixture()
def orchestrator_factory():
    """Factory that creates an Orchestrator with a custom routing return value."""
    def _make(routing_return):
        with (
            patch("jarvis_core.orchestrator.RouterLLM") as MockRouter,
            patch("jarvis_core.orchestrator.KnowledgeAgent"),
            patch("jarvis_core.orchestrator.MediaAgent"),
            patch("jarvis_core.orchestrator.SystemAgent"),
            patch("jarvis_core.orchestrator.WebAgent"),
        ):
            MockRouter.return_value.route_command.return_value = routing_return
            from jarvis_core.orchestrator import Orchestrator
            orch = Orchestrator(session_id="test-orch")

        # Set up mock return values
        orch.knowledge_agent.handle.return_value = "Knowledge answer"
        orch.knowledge_agent.stream_handle.return_value = iter(["Knowledge answer"])
        orch.media_agent.play_song.return_value = "Playing song."
        orch.system_agent.handle.return_value = "Volume muted."
        orch.web_agent.handle.return_value = "Web answer."

        # Patch router directly on the instance
        orch.router = MagicMock()
        orch.router.route_command.return_value = routing_return
        return orch

    return _make


class TestOrchestratorRouting:
    """Orchestrator routes commands to the correct agent."""

    def test_media_routing_decision(self, orchestrator_factory):
        routing = {"agent": "MediaAgent", "confidence": 0.9, "search_query_hint": None}
        orch = orchestrator_factory(routing)
        info = orch.get_routing_decision("play shape of you")
        assert info["agent"] == "MediaAgent"
        assert orch.state.active_agent == "MediaAgent"

    def test_system_routing_decision(self, orchestrator_factory):
        routing = {"agent": "SystemAgent", "confidence": 0.85, "search_query_hint": None}
        orch = orchestrator_factory(routing)
        info = orch.get_routing_decision("mute volume")
        assert info["agent"] == "SystemAgent"
        assert orch.state.active_agent == "SystemAgent"

    def test_knowledge_routing_decision(self, orchestrator_factory):
        routing = {"agent": "KnowledgeAgent", "confidence": 0.99, "search_query_hint": None}
        orch = orchestrator_factory(routing)
        info = orch.get_routing_decision("who is Einstein")
        assert info["agent"] == "KnowledgeAgent"
        assert orch.state.active_agent == "KnowledgeAgent"

    def test_run_agent_calls_media(self, orchestrator_factory):
        routing = {"agent": "MediaAgent", "confidence": 0.9, "search_query_hint": None}
        orch = orchestrator_factory(routing)
        result = orch.run_agent("play shape of you", routing)
        assert isinstance(result, str)
        orch.media_agent.play_song.assert_called_once()

    def test_run_agent_calls_system(self, orchestrator_factory):
        routing = {"agent": "SystemAgent", "confidence": 0.85, "search_query_hint": None}
        orch = orchestrator_factory(routing)
        result = orch.run_agent("mute volume", routing)
        assert isinstance(result, str)
        orch.system_agent.handle.assert_called_once()

    def test_stream_agent_knowledge(self, orchestrator_factory):
        routing = {"agent": "KnowledgeAgent", "confidence": 0.99, "search_query_hint": None}
        orch = orchestrator_factory(routing)
        chunks = list(orch.stream_agent("who is Einstein", routing))
        assert len(chunks) > 0


# ── Fix 8: memory module ──────────────────────────────────────────────────────

@pytest.fixture()
def mem(tmp_path, monkeypatch):
    """Memory module backed by a temp SQLite file."""
    import jarvis_core.memory as mem_module
    db_file = str(tmp_path / "test_memory.db")
    monkeypatch.setattr(mem_module, "_DB_PATH", db_file)
    mem_module._init_db()
    return mem_module


class TestMemory:
    """SQLite memory module: round-trip load/store."""

    def test_empty_history_for_new_session(self, mem):
        assert mem.load_history("brand-new-session") == []

    def test_append_and_load(self, mem):
        mem.append_turn("s1", "User", "hello")
        mem.append_turn("s1", "Jarvis", "hi there")
        history = mem.load_history("s1")
        assert len(history) == 2
        assert history[0] == {"role": "User", "content": "hello"}
        assert history[1] == {"role": "Jarvis", "content": "hi there"}

    def test_cap_at_max_history(self, mem):
        for i in range(mem.MAX_HISTORY + 5):
            mem.append_turn("s2", "User", f"msg {i}")
        assert len(mem.load_history("s2")) <= mem.MAX_HISTORY

    def test_sessions_are_isolated(self, mem):
        mem.append_turn("sa", "User", "session A")
        mem.append_turn("sb", "User", "session B")
        assert mem.load_history("sa") == [{"role": "User", "content": "session A"}]
        assert mem.load_history("sb") == [{"role": "User", "content": "session B"}]

    def test_clear_session(self, mem):
        mem.append_turn("s3", "User", "test")
        mem.clear_session("s3")
        assert mem.load_history("s3") == []


# ── Live integration tests (skipped without API keys) ─────────────────────────

LIVE_AI_AVAILABLE = bool(os.getenv("GROQ_API_KEY") or os.getenv("OPENROUTER_API_KEY"))


@pytest.mark.skipif(not LIVE_AI_AVAILABLE, reason="No API key (set GROQ_API_KEY or OPENROUTER_API_KEY)")
class TestLiveKnowledgeAgent:
    """Integration tests with real LLM calls — skipped in CI without keys."""

    def setup_method(self):
        from jarvis_core.agents.knowledge_agent import KnowledgeAgent
        self.agent = KnowledgeAgent(session_id="live-test")

    def test_live_handle_returns_nonempty(self):
        result = self.agent.handle("what is 2 + 2")
        assert isinstance(result, str) and len(result) > 0

    def test_live_greeting(self):
        result = self.agent.handle("hello")
        assert isinstance(result, str) and len(result) > 0
