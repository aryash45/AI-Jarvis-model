try:
    from googlesearch import search
    print("googlesearch imported successfully")
    results = list(search("test", num_results=1, advanced=True))
    print(f"Results: {results}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
