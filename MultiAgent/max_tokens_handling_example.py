"""
Max Tokens Handling

Demonstrates how to properly detect and handle scenarios where the model
generation hits the max_tokens limit. It automatically issues follow-up
prompts to smoothly resume the generation exactly where the model left off.
"""

import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

def demonstrate_text_continuation():
    """
    Shows how a low max_tokens cuts off a response and how to use
    Assistant Prefilling to force Claude to continue exactly where it left off.
    """
    print(f"{'='*80}")
    print("EXAMPLE 1: TEXT CONTINUATION AFTER MAX_TOKENS TRUNCATION")
    print(f"{'='*80}\n")
    
    # We ask for a long response but set a tiny max_tokens (e.g., 20)
    messages = [
        {"role": "user", "content": "Write a 3-paragraph story about a brave knight exploring a dark cave."}
    ]
    
    print("1. Sending initial request with max_tokens=20...")
    response1 = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=20,
        messages=messages
    )
    
    truncated_text = response1.content[0].text
    stop_reason = response1.stop_reason
    
    print(f"\n[Response 1 Stop Reason]: '{stop_reason}'")
    print(f"[Response 1 Text]: '{truncated_text}'\n(Notice it is cut off violently mid-sentence!)")
    
    # Standard architectural check for truncation
    if stop_reason == "max_tokens":
        print("\n2. Catching the 'max_tokens' stop_reason. Stitching the prompt to continue...")
        
        # We append the assistant's partial response to the history.
        # By ending the messages array with an 'assistant' turn, Claude 
        # treats this as a "prefill" and continues generating from that exact point.
        messages.append({"role": "assistant", "content": truncated_text})
        
        response2 = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=100,
            messages=messages
        )
        
        continued_text = response2.content[0].text
        print(f"\n[Response 2 Stop Reason]: '{response2.stop_reason}'")
        print(f"[Response 2 Text]: '{continued_text}'")
        
        print("\n[Full Stitched Story]:")
        # We manually stitch the partial response and the continuation together
        print(truncated_text + continued_text)


def demonstrate_json_recovery():
    """
    Shows the dangerous programmatic impact of max_tokens: corrupted JSON outputs.
    Demonstrates recovering it via the same prefill mechanism.
    """
    print(f"\n\n{'='*80}")
    print("EXAMPLE 2: JSON CONTINUATION AND RECOVERY")
    print(f"{'='*80}\n")
    
    prompt = (
        "Generate a JSON object containing a 'planets' array with 3 fictional planets. "
        "Each planet should have a 'name', 'climate', and 'population'. "
        "Output ONLY valid JSON and no markdown formatting."
    )
    
    messages = [{"role": "user", "content": prompt}]
    
    print("1. Requesting strict JSON with max_tokens=35...")
    response1 = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=35,
        messages=messages
    )
    
    broken_json = response1.content[0].text
    print(f"\n[Response 1 Stop Reason]: '{response1.stop_reason}'")
    print(f"[Broken JSON]:\n{broken_json}")
    
    # Prove that the JSON is broken and will crash a pipeline
    try:
        json.loads(broken_json)
    except json.JSONDecodeError as e:
        print(f"\n[ERROR] JSONDecodeError caught! The JSON is corrupted due to the max_tokens guillotine.")
    
    if response1.stop_reason == "max_tokens":
        print("\n2. Continuing the JSON generation using Assistant Prefill...")
        
        messages.append({"role": "assistant", "content": broken_json})
        
        response2 = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=200,
            messages=messages
        )
        
        rest_of_json = response2.content[0].text
        
        # Stitch it together
        full_json_str = broken_json + rest_of_json
        
        # Clean up any markdown blocks Claude might have added
        clean_json_str = full_json_str.strip().strip("`")
        if clean_json_str.startswith("json"):
            clean_json_str = clean_json_str[4:].strip()
        
        print(f"\n[Full Stitched JSON]:\n{full_json_str}")
        
        try:
            parsed_data = json.loads(clean_json_str)
            print(f"\n[SUCCESS] Successfully parsed stitched JSON! Found {len(parsed_data.get('planets', []))} planets.")
        except json.JSONDecodeError:
            print("\n[ERROR] Still failed to parse. Sometimes continuation needs extra care for JSON.")

if __name__ == "__main__":
    demonstrate_text_continuation()
    demonstrate_json_recovery()
