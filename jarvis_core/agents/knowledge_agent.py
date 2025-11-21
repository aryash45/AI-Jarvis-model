from jarvis_core.tools.browser_tools import BrowserTools
import wikipedia

class KnowledgeAgent:
    def __init__(self):
        self.browser = BrowserTools()

    def handle(self, command: str) -> str:
        """
        Handles general knowledge queries, definitions, and quick facts.
        """
        print(f"🧠 Knowledge Agent processing: {command}")
        
        # 1. Try Wikipedia for direct definitions/people/places
        # Heuristic: If it's a "who is", "what is", "tell me about" query
        if any(x in command.lower() for x in ["who is", "what is", "tell me about", "define"]):
            try:
                # Clean command for wiki search
                query = command.lower().replace("who is", "").replace("what is", "").replace("tell me about", "").replace("define", "").strip()
                summary = wikipedia.summary(query, sentences=2)
                return f"According to Wikipedia: {summary}"
            except wikipedia.exceptions.DisambiguationError:
                pass # Fallback to Bing
            except wikipedia.exceptions.PageError:
                pass # Fallback to Bing
            except Exception as e:
                print(f"Wiki error: {e}")

        # 2. Fallback to Bing Search for latest info or specific questions
        print("Searching Bing for answer...")
        results = self.browser.search_urls(command, num_results=3)
        
        if not results or results[0].startswith("Error"):
            return "I couldn't find any information on that."
            
        # In a real "Edge" integration, we would parse the "Snippet" from the search result.
        # Since our scraper returns URLs, we'll visit the first non-YouTube URL to get a snippet.
        # For now, let's return the top result title/link as a "Quick Answer".
        
        # TODO: Enhance BrowserTools to return Titles/Snippets, not just URLs.
        # For now, we will just open the top result for the user.
        
        top_link = results[0]
        self.browser.open_url(top_link)
        return f"I found this for you: {top_link}"
