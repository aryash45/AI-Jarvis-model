from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from jarvis_core.tools.browser_tools import BrowserTools
import logging
import os

logging.basicConfig(
    filename='logs/jarvis_security.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class KnowledgeAgent:
    """
    AI-powered knowledge agent that synthesizes answers from multiple sources.
    Uses LangChain + Groq (primary) / OpenRouter (fallback) + DuckDuckGo search.
    """

    def __init__(self):
        self.browser = BrowserTools()
        self.history = []

        groq_key    = os.getenv("GROQ_API_KEY", "")
        or_key      = os.getenv("OPENROUTER_API_KEY", "")

        # Build provider configs: Groq first (generous free tier), then OpenRouter
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
            print(f"[KnowledgeAgent] OpenRouter key found — OR fallbacks added")
        else:
            print("[KnowledgeAgent] ⚠️  No OPENROUTER_API_KEY — skipping OpenRouter")

        self.model_names = [p[0] for p in providers]
        print(f"[KnowledgeAgent] Provider chain: {self.model_names}")

        try:
            self._llm_clients = [
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
            print(f"[KnowledgeAgent] ✅ Ready with {len(self._llm_clients)} models")
        except Exception as e:
            print(f"[KnowledgeAgent] ❌ INIT FAILED: {type(e).__name__}: {str(e)}")
            logging.warning(f"KnowledgeAgent init failed: {e}")
            self.enabled = False

    def handle(self, command: str) -> str:
        """
        Answer questions using LangChain + live web search synthesis + conversational memory.
        """
        print(f"🧠 Knowledge Agent processing: {command}")
        logging.info(f"KnowledgeAgent handling: {command[:100]}")
        
        question = self._extract_question(command)
        
        if not self.enabled:
            return "Knowledge Agent is currently disabled due to LLM initialization failure. Please set OPENROUTER_API_KEY."
        
        # Step 1: Contextualize the question for search if we have history
        live_search_content = ""
        search_results = []
        is_casual = any(word in question.lower() for word in ["hi", "hello", "how are you", "who are you", "thanks", "thank you"])
        
        search_query = question
        if len(self.history) > 0 and not is_casual:
            history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.history[-4:]]) # last 4 msgs
            query_prompt = (
                "Given the conversation history, rewrite the user's latest question to be a standalone web search query. "
                "Include necessary subjects (like 'WW2' or 'Poland'). "
                "If the question is already self-contained, return it as is. "
                "ONLY return the search query, nothing else.\n\n"
                f"History:\n{history_str}\n\n"
                f"Latest Question: {question}\n\n"
                "Search Query:"
            )
            try:
                search_query = self._call_llm(query_prompt).content.strip().replace('"', '')
                logging.info(f"Contextualized search query: {search_query}")
            except Exception as e:
                logging.warning(f"Query contextualization failed: {str(e)}")
                search_query = question

        if not is_casual:
            try:
                live_search_content = self.web_search.run(search_query)
                # Skipped internal browser tools scraping to drastically improve latency.
                # DuckDuckGo snippet is usually enough.
            except Exception as e:
                logging.warning(f"DuckDuckGo search tool failed: {str(e)}")
            
        # Step 3: Synthesize final answer using the LLM with conversational memory
        answer = self._synthesize_answer(question, live_search_content, search_results)
        
        return answer
    
    def _call_llm(self, prompt_or_messages):
        """Try each provider/model in order, falling back on 429/400 errors."""
        last_error = None
        for i, client in enumerate(self._llm_clients):
            try:
                result = client.invoke(prompt_or_messages)
                if i > 0:
                    logging.info(f"Fallback succeeded with model: {self.model_names[i]}")
                return result
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "400" in err_str or "rate" in err_str.lower():
                    logging.warning(f"Model {self.model_names[i]} failed ({err_str[:80]}), trying next...")
                    last_error = e
                    continue
                raise  # Non-retryable errors bubble up immediately
        raise last_error  # All models exhausted

    def _extract_question(self, command: str) -> str:
        """Clean up command to extract the actual question"""
        question = command.lower()
        for phrase in ["search for"]:
            question = question.replace(phrase, "").strip()
        
        return question if question else command
    
    def _get_search_context(self, query: str, num_results: int = 2) -> list:
        """Get additional web search results for context using internal BrowserTools"""
        try:
            urls = self.browser.search_urls(query, num_results=num_results)
            
            if urls and not urls[0].startswith("Error"):
                search_context = []
                for url in urls:
                    try:
                        content = self.browser.fetch_page_content(url)
                        if content and not content.startswith("Error"):
                            search_context.append({
                                "url": url,
                                "content": content[:800] # First 800 chars
                            })
                    except:
                        continue
                return search_context
            return []
        except Exception as e:
            logging.error(f"Search context error: {str(e)}")
            return []
    
    def _synthesize_answer(self, question: str, live_search_content: str, search_results: list) -> str:
        """Use LangChain to create a comprehensive answer from all internet sources and chat history"""
        
        # Append user message to history
        self.history.append({"role": "User", "content": question})
        if len(self.history) > 10:  # Keep last 10 messages for memory context
            self.history = self.history[-10:]
            
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.history[:-1]])
        
        context_parts = []
        if live_search_content:
            context_parts.append(f"Web Search Results:\n{live_search_content}")
        
        if search_results:
            for i, result in enumerate(search_results, 1):
                context_parts.append(f"Source {i}:\n{result['content'][:500]}")
        
        combined_context = "\n\n".join(context_parts)
        
        prompt_template = PromptTemplate.from_template(
            "You are Jarvis, a highly intelligent, conversational, and human-like AI assistant. "
            "You must respond to the user as if you were a knowledgeable friend having a natural, flowing conversation. "
            "NEVER use robotic formatting like markdown tables, rigid bulleted lists, or textbook-style headers. "
            "Instead, weave facts and information naturally into conversational paragraphs. Be articulate, engaging, and concise.\n\n"
            "Here is the recent conversation history for context:\n"
            "{history}\n\n"
            "Here is real-time internet context (if any):\n"
            "{context}\n\n"
            "User's latest message: {question}\n\n"
            "Respond organically. If it's a casual greeting, chat normally. If it's a factual question, summarize the internet context naturally and concisely in your own words. Keep your answers brief and straight to the point to reduce generation time."
        )
        
        # Build the prompt string directly so we can use _call_llm with fallback
        prompt_str = prompt_template.format(
            question=question,
            context=combined_context,
            history=history_str
        )
        
        try:
            response = self._call_llm(prompt_str)
            logging.info("Successfully synthesized answer using LangChain")
            
            # Save AI response to history
            self.history.append({"role": "Jarvis", "content": response.content})
            return response.content
            
        except Exception as e:
            logging.error(f"LangChain synthesis failed: {str(e)}")
            if live_search_content:
                fallback = f"Here is what I found on the web: {live_search_content[:200]}..."
            else:
                fallback = "I couldn't find enough information to answer that question."
                
            self.history.append({"role": "Jarvis", "content": fallback})
            return fallback
