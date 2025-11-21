import time
from jarvis_core.tools.speech_tools import SpeechTools
from jarvis_core.orchestrator import Orchestrator

def main():
    # Initialize Tools and Orchestrator
    speech = SpeechTools()
    orchestrator = Orchestrator()
    
    speech.speak("Initializing Jarvis 2025 Agent System.")
    print("Jarvis 2025 System Initialized.")

    while True:
        try:
            # Listen for activation
            # For simplicity in this version, we listen for any command if the script is running
            # In a real deployment, we'd use a wake word engine like Porcupine or a simple loop
            
            print("Listening for command...")
            command = speech.listen("Waiting for command...")
            
            if not command:
                continue

            print(f"User said: {command}")
            
            if "exit" in command or "stop" in command:
                speech.speak("Shutting down.")
                break

            # Process Command using route_command (not process_command)
            response = orchestrator.route_command(command)
            
            # Speak Response
            if response:
                print(f"Jarvis: {response}")
                speech.speak(response)

        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            speech.speak("I encountered an error.")

if __name__ == "__main__":
    main()
