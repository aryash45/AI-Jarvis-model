from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from jarvis_core.tools.browser_tools import BrowserTools
from jarvis_core import memory as mem
import logging
import os
from typing import Iterator, Optional, List

logging.basicConfig(
    filename='logs/jarvis_security.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class KnowledgeAgent:
    """
    AI-powered knowledge agent that synthesizes answers from multiple sources.
    Uses LangChain + Groq (primary) / OpenRouter (fallback) + DuckDuckGo search.

    Changes (this revision):
    - Fix 4: accepts ``search_query_hint`` from RouterLLM to skip the separate
      query-contextualization LLM call when one has already been provided.
    - Fix 5: ``stream_handle()`` yields text chunks via LangChain ``.stream()``.
    - Fix 7: history is loaded from / saved to SQLite via ``jarvis_core.memory``.
    """

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.browser = BrowserTools()

        # ── Load persisted history ────────────────────────────────────────────
        self.history: List[dict] = mem.load_history(session_id)

        groq_key = os.getenv("GROQ_API_KEY", "")
        or_key   = os.getenv("OPENROUTER_API_KEY", "")

        providers = []

        if groq_key:
            for model in [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
                "gemma2-9b-it",
            ]:
                providers.append((model, groq_key, "https://api.groq.com/openai/v1"))
            print(f"[KnowledgeAgent] Groq key found — {len(providers)} Groq models queued")
        else:
            print("[KnowledgeAgent] ⚠️  No GROQ_API_KEY — skipping Groq")

        if or_key:
            for model in [
                "meta-llama/llama-3.3-70b-instruct:free",
                "meta-llama/llama-3.2-3b-instruct:free",
                "nvidia/nemotron-3-super-120b-a12b:free",
            ]:
                providers.append((model, or_key, "https://openrouter.ai/api/v1"))
            print("[KnowledgeAgent] OpenRouter key found — OR fallbacks added")
        else:
            print("[KnowledgeAgent] ⚠️  No OPENROUTER_API_KEY — skipping OpenRouter")

        self.model_names = [p[0] for p in providers]
        print(f"[KnowledgeAgent] Provider chain: {self.model_names}")

        try:
            self._llm_clients: List[ChatOpenAI] = [
                ChatOpenAI(
                    model=model,
                    openai_api_key=key,
                    openai_api_base=base_url,
                    temperature=0.3,
                    max_retries=0,
                )
                for model, key, base_url in providers
            ]
            self.llm = self._llm_clients[0] if self._llm_clients else None
            self.web_search = DuckDuckGoSearchRun()
            self.enabled = bool(self._llm_clients)
            print(f"[KnowledgeAgent] ✅ Ready with {len(self._llm_clients)} models "
                  f"(session={session_id}, history={len(self.history)} msgs)")
        except Exception as e:
            print(f"[KnowledgeAgent] ❌ INIT FAILED: {type(e).__name__}: {e}")
            logger.warning("KnowledgeAgent init failed: %s", e)
            self.enabled = False

    # ── Public entry points ───────────────────────────────────────────────────

    def handle(self, command: str, search_query_hint: Optional[str] = None) -> str:
        """
        Blocking answer — returns the full response string.
        ``search_query_hint`` (from RouterLLM tool call) skips the separate
        query-contextualization LLM call when provided.
        """
        return "".join(self.stream_handle(command, search_query_hint=search_query_hint))

    def stream_handle(
        self,
        command: str,
        search_query_hint: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Streaming answer — yields text chunks as they arrive from the LLM.
        Falls back to a single yield on error.

        Fix 4: uses ``search_query_hint`` from the routing call to skip the
        separate query-contextualization round-trip when history is short or a
        hint is already available.
        Fix 5: uses LangChain ``.stream()`` instead of ``.invoke()``.
        """
        print(f"🧠 Knowledge Agent processing (stream): {command}")
        logger.info("KnowledgeAgent streaming: %s", command[:100])

        question = self._extract_question(command)

        if not self.enabled:
            yield ("Knowledge Agent is currently disabled due to LLM initialization failure. "
                   "Please set OPENROUTER_API_KEY.")
            return

        # ── Step 1: Determine search query ────────────────────────────────────
        is_casual = any(
            word in question.lower()
            for word in ["hi", "hello", "how are you", "who are you", "thanks", "thank you"]
        )

        # Fix 4: skip contextualization if:
        #   (a) a hint was already produced by the router call, OR
        #   (b) history is empty (nothing to disambiguate), OR
        #   (c) it's a casual greeting
        if search_query_hint:
            search_query = search_query_hint
            logger.info("Using router-provided search_query_hint: %s", search_query)
        elif len(self.history) > 0 and not is_casual:
            history_str = "\n".join(
                f"{msg['role']}: {msg['content']}" for msg in self.history[-4:]
            )
            query_prompt = (
                "Given the conversation history, rewrite the user's latest question "
                "to be a standalone web search query. Include necessary subjects "
                "(like 'WW2' or 'Poland'). If the question is already self-contained, "
                "return it as is. ONLY return the search query, nothing else.\n\n"
                f"History:\n{history_str}\n\n"
                f"Latest Question: {question}\n\n"
                "Search Query:"
            )
            try:
                search_query = self._call_llm(query_prompt).content.strip().replace('"', '')
                logger.info("Contextualized search query: %s", search_query)
            except Exception as e:
                logger.warning("Query contextualization failed: %s", e)
                search_query = question
        else:
            # Empty history or casual — no extra call needed
            search_query = question

        # ── Step 2: Web search ────────────────────────────────────────────────
        live_search_content = ""
        if not is_casual:
            try:
                live_search_content = self.web_search.run(search_query)
            except Exception as e:
                logger.warning("DuckDuckGo search failed: %s", e)

        # ── Step 3: Build prompt ──────────────────────────────────────────────
        self.history.append({"role": "User", "content": question})
        if len(self.history) > mem.MAX_HISTORY:
            self.history = self.history[-mem.MAX_HISTORY:]

        # Persist user turn
        mem.append_turn(self.session_id, "User", question)

        history_str = "\n".join(
            f"{msg['role']}: {msg['content']}" for msg in self.history[:-1]
        )

        context_parts = []
        if live_search_content:
            context_parts.append(f"Web Search Results:\n{live_search_content}")

        combined_context = "\n\n".join(context_parts)

        prompt_template = PromptTemplate.from_template(
            "You are Jarvis, a highly intelligent, conversational, and human-like AI assistant. "
            "You must respond to the user as if you were a knowledgeable friend having a natural, "
            "flowing conversation. NEVER use robotic formatting like markdown tables, rigid bulleted "
            "lists, or textbook-style headers. Instead, weave facts and information naturally into "
            "conversational paragraphs. Be articulate, engaging, and concise.\n\n"
            "Here is the recent conversation history for context:\n"
            "{history}\n\n"
            "Here is real-time internet context (if any):\n"
            "{context}\n\n"
            "User's latest message: {question}\n\n"
            "Respond organically. If it's a casual greeting, chat normally. If it's a factual "
            "question, summarize the internet context naturally and concisely in your own words. "
            "Keep your answers brief and straight to the point to reduce generation time."
        )

        prompt_str = prompt_template.format(
            question=question,
            context=combined_context,
            history=history_str,
        )

        # ── Step 4: Stream response ───────────────────────────────────────────
        full_response = ""
        try:
            for chunk in self._stream_llm(prompt_str):
                full_response += chunk
                yield chunk

            logger.info("KnowledgeAgent streaming complete")
        except Exception as e:
            logger.error("KnowledgeAgent streaming failed: %s", e)
            if live_search_content:
                fallback = f"Here is what I found on the web: {live_search_content[:200]}..."
            else:
                fallback = "I couldn't find enough information to answer that question."
            full_response = fallback
            yield fallback

        # ── Persist Jarvis reply ──────────────────────────────────────────────
        self.history.append({"role": "Jarvis", "content": full_response})
        if len(self.history) > mem.MAX_HISTORY:
            self.history = self.history[-mem.MAX_HISTORY:]
        mem.append_turn(self.session_id, "Jarvis", full_response)

    # ── LLM helpers ───────────────────────────────────────────────────────────

    def _call_llm(self, prompt_or_messages):
        """Try each provider/model in order, falling back on 429/400 errors."""
        last_error = None
        for i, client in enumerate(self._llm_clients):
            try:
                result = client.invoke(prompt_or_messages)
                if i > 0:
                    logger.info("KnowledgeAgent fallback succeeded: %s", self.model_names[i])
                return result
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "400" in err_str or "rate" in err_str.lower():
                    logger.warning(
                        "Model %s failed (%s…), trying next",
                        self.model_names[i],
                        err_str[:80],
                    )
                    last_error = e
                    continue
                raise
        raise last_error or RuntimeError("KnowledgeAgent._call_llm: all models exhausted with no error captured")

    def _stream_llm(self, prompt: str) -> Iterator[str]:
        """
        Try each provider/model in order using streaming mode.
        Yields text chunks. Falls back to next model on 429/400 errors.
        """
        last_error = None
        for i, client in enumerate(self._llm_clients):
            try:
                for chunk in client.stream(prompt):
                    text = chunk.content if hasattr(chunk, "content") else str(chunk)
                    if text:
                        yield text
                return  # success — stop trying further models
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "400" in err_str or "rate" in err_str.lower():
                    logger.warning(
                        "Streaming model %s failed (%s…), trying next",
                        self.model_names[i],
                        err_str[:80],
                    )
                    last_error = e
                    continue
                raise
        raise last_error or RuntimeError("KnowledgeAgent._stream_llm: all models exhausted with no error captured")

    # ── Misc helpers ──────────────────────────────────────────────────────────

    def _extract_question(self, command: str) -> str:
        """Clean up command to extract the actual question."""
        question = command.lower()
        for phrase in ["search for"]:
            question = question.replace(phrase, "").strip()
        return question if question else command

    def _get_search_context(self, query: str, num_results: int = 2) -> list:
        """Get additional web search results using internal BrowserTools."""
        try:
            urls = self.browser.search_urls(query, num_results=num_results)
            if urls and not urls[0].startswith("Error"):
                search_context = []
                for url in urls:
                    try:
                        content = self.browser.fetch_page_content(url)
                        if content and not content.startswith("Error"):
                            search_context.append({"url": url, "content": content[:800]})
                    except Exception:
                        continue
                return search_context
            return []
        except Exception as e:
            logger.error("Search context error: %s", e)
            return []
