from jarvis_core.agents.research_agent import ResearchAgent

def test_research():
    import sys
    import os
    
    # Redirect stdout and stderr to a file
    with open("full_log.txt", "w", encoding="utf-8") as log_file:
        sys.stdout = log_file
        sys.stderr = log_file
        
        print(f"CWD: {os.getcwd()}")
        try:
            agent = ResearchAgent()
            print("Testing Research Agent...")
            result = agent.research("why did the indus valley civilization disappear")
            print("\nRESULT:")
            print(result)
        except Exception as e:
            print(f"EXCEPTION: {e}")
        finally:
            # Restore stdout/stderr (optional, but good practice)
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

if __name__ == "__main__":
    test_research()

if __name__ == "__main__":
    test_research()
