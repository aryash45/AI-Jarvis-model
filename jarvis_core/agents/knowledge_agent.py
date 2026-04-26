from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
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
    Uses LangChain, Ollama, and DuckDuckGo for live internet search.
    """
    
    def __init__(self):
        self.browser = BrowserTools()
        self.history = []  # Added conversational memory
        
        # Initialize Langchain components
        model_name = os.getenv("OLLAMA_MODEL", "llama3")
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        try:
            self.llm = ChatOllama(model=model_name, base_url=ollama_host, temperature=0.3)
            # Upgraded from Wikipedia to live DuckDuckGo Search
            self.web_search = DuckDuckGoSearchRun()
            self.enabled = True
        except Exception as e:
            logging.warning(f"Failed to initialize LangChain Ollama in KnowledgeAgent: {str(e)}")
            self.enabled = False

    def handle(self, command: str) -> str:
        """
        Answer questions using LangChain + live web search synthesis + conversational memory.
        """
        print(f"🧠 Knowledge Agent processing: {command}")
        logging.info(f"KnowledgeAgent handling: {command[:100]}")
        
        question = self._extract_question(command)
        
        if not self.enabled:
            return "Knowledge Agent is currently disabled due to LLM initialization failure."
        
        # Step 1: Only run web search if the query seems to need facts (skip for casual chat)
        live_search_content = ""
        search_results = []
        is_casual = any(word in question.lower() for word in ["hi", "hello", "how are you", "who are you", "thanks", "thank you"])
        
        if not is_casual:
            try:
                live_search_content = self.web_search.run(question)
                # Step 2: Use internal browser tools for deeper context (fallback)
                search_results = self._get_search_context(question)
            except Exception as e:
                logging.warning(f"DuckDuckGo search tool failed: {str(e)}")
            
        # Step 3: Synthesize final answer using the LLM with conversational memory
        answer = self._synthesize_answer(question, live_search_content, search_results)
        
        return answer
    
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
            "Respond organically. If it's a casual greeting, chat normally. If it's a factual question, summarize the internet context naturally in your own words, avoiding lists."
        )
        
        chain = prompt_template | self.llm
        
        try:
            response = chain.invoke({"question": question, "context": combined_context, "history": history_str})
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
