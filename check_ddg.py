try:
    from duckduckgo_search import DDGS
    print("DDGS imported successfully")
    with DDGS() as ddgs:
        results = list(ddgs.text("test", max_results=3))
        print(f"Results found: {len(results)}")
        for r in results:
            print(r)
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
