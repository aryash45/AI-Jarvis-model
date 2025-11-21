from jarvis_core.orchestrator import Orchestrator

def test_agents():
    orchestrator = Orchestrator()
    
    print("Testing Jarvis 2025 Agent System\n")
    
    # Test 1: Knowledge Agent
    print("1. Testing Knowledge Agent:")
    result = orchestrator.route_command("who is Albert Einstein")
    print(f"   Result: {result}\n")
    
    # Test 2: Media Agent
    print("2. Testing Media Agent:")
    result = orchestrator.route_command("play shape of you")
    print(f"   Result: {result}\n")
    
    # Test 3: System Agent
    print("3. Testing System Agent:")
    result = orchestrator.route_command("mute volume")
    print(f"   Result: {result}\n")
    
    print("All tests completed!")

if __name__ == "__main__":
    test_agents()
