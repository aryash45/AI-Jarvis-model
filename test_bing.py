from jarvis_core.tools.browser_tools import BrowserTools

def test_bing():
    bt = BrowserTools()
    print("Testing Bing Search...")
    
    # Test 1: General Search
    query = "how the Roman Empire collapsed"
    print(f"\nSearching for: {query}")
    results = bt.search_urls(query, num_results=3)
    print("Results:")
    for r in results:
        print(f"- {r}")

    # Test 2: YouTube Search (for MediaAgent)
    query2 = "play shape of you youtube"
    print(f"\nSearching for: {query2}")
    results2 = bt.search_urls(query2, num_results=3)
    print("Results:")
    for r in results2:
        print(f"- {r}")

if __name__ == "__main__":
    test_bing()
