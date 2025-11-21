from bs4 import BeautifulSoup
import webbrowser
import requests
from typing import Optional

class BrowserTools:
    @staticmethod
    def open_url(url: str) -> str:
        """Opens a URL in the default web browser."""
        try:
            webbrowser.open(url)
            return f"Successfully opened {url}"
        except Exception as e:
            return f"Failed to open URL: {str(e)}"

    @staticmethod
    def google_search(query: str) -> str:
        """Opens a Google search for the query."""
        url = f"https://www.google.com/search?q={'+'.join(query.split())}"
        return BrowserTools.open_url(url)

    @staticmethod
    def search_urls(query: str, num_results: int = 3) -> list[str]:
        """Searches Bing and returns a list of URLs."""
        # Use Bing (Edge) Search via scraping
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            search_url = f"https://www.bing.com/search?q={query}"
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Bing search results are usually in <li class="b_algo">
            for item in soup.find_all('li', class_='b_algo'):
                link_tag = item.find('a')
                if link_tag and 'href' in link_tag.attrs:
                    href = link_tag['href']
                    if href.startswith('http'):
                        results.append(href)
                        if len(results) >= num_results:
                            break
            
            if not results:
                return ["Error: No results found on Bing."]
                
            return results
            
        except Exception as e:
            return [f"Error searching Bing: {e}"]

    @staticmethod
    def fetch_page_content(url: str) -> str:
        """Fetches and cleans text content from a URL."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Use BeautifulSoup to clean HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
                
            text = soup.get_text()
            
            # Break into lines and remove leading/trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text[:10000] # Increased limit for research
        except Exception as e:
            return f"Error fetching page: {str(e)}"
