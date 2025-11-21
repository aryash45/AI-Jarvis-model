from jarvis_core.tools.browser_tools import BrowserTools
import wikipedia

class WebAgent:
    def __init__(self):
        self.browser = BrowserTools()

    def handle(self, command: str) -> str:
        """
        Unified handler for general web commands (fallback).
        """
        command_lower = command.lower()
        
        # Check for specific keywords
        if "wikipedia" in command_lower:
            topic = command_lower.replace("wikipedia", "").strip()
            return self.handle_wikipedia(topic)
        elif "news" in command_lower:
            return self.handle_news()
        elif "search" in command_lower:
            query = command_lower.replace("search", "").strip()
            return self.handle_search(query)
        else:
            # Default: just do a Google search
            return self.handle_search(command)

    def handle_search(self, query: str) -> str:
        """Handles general web search."""
        return self.browser.google_search(query)

    def handle_wikipedia(self, topic: str) -> str:
        """Handles Wikipedia summaries."""
        try:
            wikipedia.set_lang("en")
            summary = wikipedia.summary(topic, sentences=2)
            return summary
        except Exception as e:
            return f"Could not find info on {topic}: {str(e)}"

    def handle_news(self) -> str:
        """Handles fetching news (placeholder for now)."""
        # In a real implementation, we'd use NewsAPI here as in the original script
        # For now, we'll just open Google News
        self.browser.open_url("https://news.google.com")
        return "Opened Google News."
