import json
from jarvis_core.tools.browser_tools import BrowserTools

class MediaAgent:
    def __init__(self):
        self.browser = BrowserTools()

    def play_song(self, query: str) -> str:
        """
        Searches for the song/video on YouTube and plays it.
        """
        print(f"[MediaAgent] Searching for: {query}")
        
        # Construct search query
        # If it's a genre request like "romantic music", append "playlist" for better results
        search_query = query
        if "music" in query.lower() or "songs" in query.lower():
             if "playlist" not in query.lower():
                 search_query += " playlist"
        
        # Search specifically on YouTube
        # "site:youtube.com" can be flaky with DDG, so we use "youtube {query}"
        full_query = f"{search_query} youtube"
        
        # Fetch more results to ensure we find a valid video link
        results = self.browser.search_urls(full_query, num_results=5)
        
        video_url = None
        if results and not results[0].startswith("Error"):
            for url in results:
                # Allow videos AND playlists
                if "youtube.com/watch" in url or "youtu.be/" in url or "youtube.com/playlist" in url:
                    video_url = url
                    break
        
        if video_url:
            self.browser.open_url(video_url)
            return f"Playing {query} on YouTube."
        else:
            # Fallback: Just open YouTube search
            fallback_url = f"https://www.youtube.com/results?search_query={query}"
            self.browser.open_url(fallback_url)
            return f"Could not find a direct link. Opening YouTube search for {query}."
