from bs4 import BeautifulSoup
import webbrowser
import requests
from typing import Optional, List, Tuple
from urllib.parse import urlparse, quote_plus
import time
import logging
from functools import lru_cache
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    filename='logs/jarvis_security.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class BrowserTools:
    # Simple cache with TTL for search results
    _search_cache = {}
    CACHE_TTL = 300  # 5 minutes in seconds
    MAX_QUERY_LENGTH = 500
    REQUEST_TIMEOUT = 10
    MAX_RETRIES = 3
    
    @staticmethod
    def _validate_url(url: str) -> bool:
        """Validates URL format and scheme."""
        try:
            result = urlparse(url)
            # Only allow http and https schemes
            return all([result.scheme in ['http', 'https'], result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def _sanitize_query(query: str) -> str:
        """Sanitizes search query input."""
        # Strip whitespace and limit length
        query = query.strip()
        if len(query) > BrowserTools.MAX_QUERY_LENGTH:
            logging.warning(f"Query truncated from {len(query)} to {BrowserTools.MAX_QUERY_LENGTH} chars")
            query = query[:BrowserTools.MAX_QUERY_LENGTH]
        return query
    
    @staticmethod
    def _get_cached_results(query: str) -> Optional[List[str]]:
        """Gets cached search results if still valid."""
        if query in BrowserTools._search_cache:
            cached_data, timestamp = BrowserTools._search_cache[query]
            if datetime.now() - timestamp < timedelta(seconds=BrowserTools.CACHE_TTL):
                logging.info(f"Cache hit for query: {query[:50]}")
                return cached_data
            else:
                # Remove expired cache entry
                del BrowserTools._search_cache[query]
        return None
    
    @staticmethod
    def _cache_results(query: str, results: List[str]):
        """Caches search results with timestamp."""
        BrowserTools._search_cache[query] = (results, datetime.now())
        
        # Simple cache size management - keep only last 50 queries
        if len(BrowserTools._search_cache) > 50:
            oldest_key = min(BrowserTools._search_cache.keys(), 
                           key=lambda k: BrowserTools._search_cache[k][1])
            del BrowserTools._search_cache[oldest_key]
    
    @staticmethod
    def open_url(url: str) -> str:
        """Opens a URL in the default web browser with validation."""
        try:
            # Validate URL format
            if not BrowserTools._validate_url(url):
                logging.warning(f"Attempted to open invalid URL: {url[:100]}")
                return f"Error: Invalid URL format"
            
            # Additional length check
            if len(url) > 2048:  # Standard max URL length
                return "Error: URL too long"
            
            webbrowser.open(url)
            logging.info(f"Opened URL: {url[:100]}")
            return f"Successfully opened {url[:100]}"
        except Exception as e:
            logging.error(f"Failed to open URL {url[:100]}: {str(e)}")
            return f"Failed to open URL: {str(e)}"

    @staticmethod
    def google_search(query: str) -> str:
        """Opens a Google search for the query with sanitization."""
        try:
            query = BrowserTools._sanitize_query(query)
            
            if not query:
                return "Error: Empty search query"
            
            # Use quote_plus for proper URL encoding
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            
            return BrowserTools.open_url(url)
        except Exception as e:
            logging.error(f"Google search failed: {str(e)}")
            return f"Search failed: {str(e)}"

    @staticmethod
    def search_urls(query: str, num_results: int = 3) -> List[str]:
        """Searches Bing and returns a list of URLs with caching and validation."""
        try:
            # Sanitize query
            query = BrowserTools._sanitize_query(query)
            
            if not query:
                return ["Error: Empty search query"]
            
            # Validate num_results
            num_results = max(1, min(num_results, 10))  # Clamp between 1-10
            
            # Check cache first
            cache_key = f"{query}:{num_results}"
            cached = BrowserTools._get_cached_results(cache_key)
            if cached:
                return cached
            
            # Prepare headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            
            # URL encode query
            encoded_query = quote_plus(query)
            search_url = f"https://www.bing.com/search?q={encoded_query}"
            
            # Exponential backoff retry logic
            for attempt in range(BrowserTools.MAX_RETRIES):
                try:
                    response = requests.get(
                        search_url, 
                        headers=headers, 
                        timeout=BrowserTools.REQUEST_TIMEOUT
                    )
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt < BrowserTools.MAX_RETRIES - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logging.warning(f"Request failed (attempt {attempt+1}), retrying in {wait_time}s: {str(e)}")
                        time.sleep(wait_time)
                    else:
                        raise
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Bing search results are usually in <li class="b_algo">
            for item in soup.find_all('li', class_='b_algo'):
                link_tag = item.find('a')
                if link_tag and 'href' in link_tag.attrs:
                    href = link_tag['href']
                    
                    # Validate URL before adding
                    if href.startswith('http') and BrowserTools._validate_url(href):
                        results.append(href)
                        if len(results) >= num_results:
                            break
            
            if not results:
                logging.warning(f"No results found for query: {query[:50]}")
                return ["Error: No results found on Bing."]
            
            # Cache the results
            BrowserTools._cache_results(cache_key, results)
            logging.info(f"Found {len(results)} results for query: {query[:50]}")
            
            return results
            
        except requests.exceptions.Timeout:
            logging.error(f"Bing search timeout for query: {query[:50]}")
            return ["Error: Search request timed out"]
        except requests.exceptions.RequestException as e:
            logging.error(f"Bing search request failed: {str(e)}")
            return [f"Error: Network request failed - {str(e)}"]
        except Exception as e:
            logging.error(f"Unexpected error in search_urls: {str(e)}")
            return [f"Error searching Bing: {str(e)}"]

    @staticmethod
    def fetch_page_content(url: str) -> str:
        """Fetches and cleans text content from a URL with validation."""
        try:
            # Validate URL
            if not BrowserTools._validate_url(url):
                logging.warning(f"Attempted to fetch invalid URL: {url[:100]}")
                return "Error: Invalid URL format"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=BrowserTools.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script, style, and navigation elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
                
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Return first 10000 characters
            result = text[:10000]
            logging.info(f"Successfully fetched {len(result)} chars from {url[:100]}")
            return result
            
        except requests.exceptions.Timeout:
            logging.error(f"Timeout fetching page: {url[:100]}")
            return "Error: Request timed out"
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch page {url[:100]}: {str(e)}")
            return f"Error: Failed to fetch page - {str(e)}"
        except Exception as e:
            logging.error(f"Unexpected error fetching page: {str(e)}")
            return f"Error fetching page: {str(e)}"
