"""
Advanced Stop Reasons

Explores complex logic based on the various stop_reasons returned by the
Anthropic API (e.g., tool_use vs. end_turn). Understanding these reasons
allows you to dictate exactly when control should return to the application vs
the user.
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"


# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

def print_section_header(title: str):
    print("\n" + "=" * 80)
    print(f"🔹 {title}")
    print("=" * 80)

def run_advanced_stop_reasons():
    # ---------------------------------------------------------
    # SCENARIO 1: Max Tokens (stop_reason == "max_tokens")
    # ---------------------------------------------------------
    print_section_header('SCENARIO 1: max_tokens')
    print("Asking Claude to write a long essay, but setting max_tokens=10...")
    
    response_max = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=10,
        messages=[{"role": "user", "content": "Write a 500-word essay about the history of Rome."}]
    )
    
    print(f"\nStop Reason: '{response_max.stop_reason}'")
    print(f"Output Text: {response_max.content[0].text}")
    print("Explanation: Claude was forced to stop mid-sentence because it hit the token limit.")


    # ---------------------------------------------------------
    # SCENARIO 2: Stop Sequence (stop_reason == "stop_sequence")
    # ---------------------------------------------------------
    print_section_header('SCENARIO 2: stop_sequence')
    print("Asking Claude to list three colors, but setting stop_sequences=['Green']...")
    
    response_seq = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=100,
        stop_sequences=["Green"],
        messages=[{"role": "user", "content": "Reply with exactly these three colors on separate lines: Red, Green, Blue."}]
    )
    
    print(f"\nStop Reason: '{response_seq.stop_reason}'")
    print(f"Output Text:\n{response_seq.content[0].text}")
    print("Explanation: Generation halted the exact moment it encountered the word 'Green'.")




    # ---------------------------------------------------------
    # SCENARIO 3: Exceeding Max Context Window
    # ---------------------------------------------------------
    print_section_header('SCENARIO 3: Max Context Window Limit')
    print("Attempting to send a prompt that is massively larger than the 200K context window...")
    
    try:
        # Generate an absurdly large string (approx 300,000 tokens)
        massive_prompt = "hello world " * 150000 
        
        response_context = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": massive_prompt}]
        )
    except Exception as e:
        print(f"\nExpected Error Caught!\n{type(e).__name__}: {e}")
        print("\nExplanation: Exceeding the maximum context window (e.g., 200,000 tokens) does NOT return a stop reason.")
        print("Instead, the API rejects the request entirely and throws an anthropic.BadRequestError before generation even starts.")

if __name__ == "__main__":
    run_advanced_stop_reasons()
