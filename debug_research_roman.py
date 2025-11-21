from jarvis_core.tools.browser_tools import BrowserTools
from duckduckgo_search import DDGS

def debug_research():
    topic = "how the Roman Empire collapsed"
    print(f"Topic: {topic}")
    
    # 1. Test Search Raw
    print("\n--- Raw Search Results ---")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(topic, max_results=5))
            for r in results:
                print(f"Title: {r.get('title')}")
                print(f"URL: {r.get('href')}")
                print(f"Body: {r.get('body')}\n")
    except Exception as e:
        print(f"Search Error: {e}")

    # 2. Test BrowserTools wrapper
    print("\n--- BrowserTools.search_urls ---")
    bt = BrowserTools()
    urls = bt.search_urls(topic, num_results=5)
    print(f"URLs found: {urls}")

    # 3. Test Scraping
    if urls and not urls[0].startswith("Error"):
        print(f"\n--- Scraping First URL: {urls[0]} ---")
        content = bt.fetch_page_content(urls[0])
        print(f"Content Preview:\n{content[:500]}")

if __name__ == "__main__":
    debug_research()
