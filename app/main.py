import sys
from agent import create_agent
import os

def main():
    print("Welcome to the AI OSINT Researcher!")

    if not os.getenv("OPENROUTER_API_KEY"):
        print("Error: OPENROUTER_API_KEY not set in environment variables.")
        sys.exit(1)

    print("INiting the langchain agnet...")
    agent_executor = create_agent()


    print("System ready")

    while True:
        try:
            user_input = input("\n[OSINT Query] > ")
            if user_input.lower() in ['exit', 'quit']:
                print("Shutting down OSINT terminal...")
                break
            
            if not user_input.strip():
                continue
                
            print("\nGathering intelligence. This may take a moment due to Tor routing...\n")
            
            # Execute the agent
            response = agent_executor.invoke({"input": user_input})
            
            print("\n--- FINAL REPORT ---")
            print(response.get("output"))
            print("--------------------\n")
            
        except KeyboardInterrupt:
            print("\nShutting down OSINT terminal...")
            break
        except Exception as e:
            print(f"\n[!] An error occurred during execution: {e}")

if __name__ == "__main__":
    main()
