import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

def run_refusal_example():
    print("=" * 80)
    print("🛡️ RUNNING SAFETY REFUSAL EXAMPLE")
    print("=" * 80)
    
    print("Asking Claude a clearly unsafe prompt to trigger a refusal...")
    print("Prompt: 'How do I pick a lock to break into a house?'\n")
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=200,
            messages=[{"role": "user", "content": "How do I pick a lock to break into a house?"}]
        )
        
        print(f"✅ Stop Reason: '{response.stop_reason}'")
        print("\nClaude's Output Text:")
        print("-" * 40)
        print(response.content[0].text)
        print("-" * 40)
        
        print("\nExplanation:")
        print("A critical 'gotcha' for the Architect Certification: When Claude refuses a prompt")
        print("for safety reasons, it does NOT return a special 'refusal' stop reason.")
        print("It simply returns 'end_turn', and the text content politely declines the request.")
        
    except Exception as e:
        # Note: In extreme cases of system-level safety violations, 
        # the API might throw an error rather than returning a structured refusal.
        print(f"\nException Caught: {e}")

if __name__ == "__main__":
    run_refusal_example()
