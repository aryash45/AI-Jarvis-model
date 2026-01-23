from jarvis_core.tools.browser_tools import BrowserTools
from jarvis_core.groq_ai import GroqAI
import wikipedia
import logging

logging.basicConfig(
    filename='logs/jarvis_security.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class KnowledgeAgent:
    """
    AI-powered knowledge agent that synthesizes answers from multiple sources.
    Works like ChatGPT but with web search!
    """
    
    def __init__(self):
        self.browser = BrowserTools()
        self.ai = GroqAI()

    def handle(self, command: str) -> str:
        """
        Answer questions using AI + web search synthesis.
        """
        print(f"🧠 Knowledge Agent processing: {command}")
        logging.info(f"KnowledgeAgent handling: {command[:100]}")
        
        # Extract the actual question from command
        question = self._extract_question(command)
        
        # Step 1: Try Wikipedia for quick facts
        wiki_content = self._try_wikipedia(question)
        
        # Step 2: Get web search results for additional context
        search_results = self._get_search_context(question)
        
        # Step 3: Use AI to synthesize a comprehensive answer
        answer = self._synthesize_answer(question, wiki_content, search_results)
        
        return answer
    
    def _extract_question(self, command: str) -> str:
        """Clean up command to extract the actual question"""
        # Remove common trigger phrases
        question = command.lower()
        for phrase in ["who is", "what is", "tell me about", "explain", "define", "search for"]:
            question = question.replace(phrase, "").strip()
        
        return question if question else command
    
    def _try_wikipedia(self, query: str) -> str:
        """Try to get Wikipedia summary"""
        try:
            wikipedia.set_lang("en")
            summary = wikipedia.summary(query, sentences=3, auto_suggest=True)
            logging.info(f"Wikipedia found content for: {query[:50]}")
            return summary
        except wikipedia.exceptions.DisambiguationError as e:
            # Multiple options - use the first one
            try:
                summary = wikipedia.summary(e.options[0], sentences=3)
                return summary
            except:
                return None
        except wikipedia.exceptions.PageError:
            logging.info(f"Wikipedia page not found for: {query[:50]}")
            return None
        except Exception as e:
            logging.warning(f"Wikipedia error: {str(e)}")
            return None
    
    def _get_search_context(self, query: str, num_results: int = 3) -> list:
        """Get web search results for context"""
        try:
            urls = self.browser.search_urls(query, num_results=num_results)
            
            if urls and not urls[0].startswith("Error"):
                # Fetch content from top results
                search_context = []
                for url in urls[:2]:  # Only fetch first 2 to save time
                    try:
                        content = self.browser.fetch_page_content(url)
                        if content and not content.startswith("Error"):
                            # Limit content size
                            search_context.append({
                                "url": url,
                                "content": content[:1000]  # First 1000 chars
                            })
                    except:
                        continue
                
                return search_context
            
            return []
            
        except Exception as e:
            logging.error(f"Search context error: {str(e)}")
            return []
    
    def _synthesize_answer(self, question: str, wiki_content: str, search_results: list) -> str:
        """Use AI to create a comprehensive answer from all sources"""
        
        # Build context from sources
        context_parts = []
        
        if wiki_content:
            context_parts.append(f"Wikipedia: {wiki_content}")
        
        if search_results:
            for i, result in enumerate(search_results, 1):
                context_parts.append(f"Source {i}: {result['content'][:500]}")
        
        if not context_parts:
            # No sources found, let AI try to answer from knowledge
            return self._ai_answer_from_knowledge(question)
        
        # Combine all context
        combined_context = "\n\n".join(context_parts)
        
        # Create prompt for AI
        prompt = f"""You are a knowledgeable assistant. Answer this question using the provided sources.

Question: {question}

Available information:
{combined_context}

Provide a clear, concise answer (2-3 sentences). If the sources don't contain enough information, say so and provide what you know."""

        try:
            answer = self.ai.chat(prompt, max_tokens=300)
            logging.info("Successfully synthesized answer using AI")
            return answer
            
        except Exception as e:
            logging.error(f"AI synthesis failed: {str(e)}")
            # Fallback to just returning Wikipedia or first search result
            if wiki_content:
                return f"According to Wikipedia: {wiki_content}"
            elif search_results:
                return f"Here's what I found: {search_results[0]['content'][:500]}..."
            else:
                return "I couldn't find enough information to answer that question."
    
    def _ai_answer_from_knowledge(self, question: str) -> str:
        """Let AI try to answer from its training knowledge when no web sources found"""
        
        prompt = f"""Answer this question concisely in 2-3 sentences:

Question: {question}

If you don't know, say "I don't have enough information about that." """

        try:
            answer = self.ai.chat(prompt, max_tokens=200)
            return answer
        except:
            return "I couldn't find information about that. Please try rephrasing your question."

