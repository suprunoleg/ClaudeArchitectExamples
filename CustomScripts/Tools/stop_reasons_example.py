"""
Basic Stop Reasons

Shows how to parse and act upon the standard stop_reasons provided in the
model's response. It provides the foundation for building basic interaction
loops.
"""

import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"


# Load environment variables (API Key)
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

# =====================================================================
# Tool Definition
# =====================================================================
get_weather_tool = {
    "name": "get_weather",
    "description": "Get the current weather in a given location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA"
            }
        },
        "required": ["location"]
    }
}

def mock_get_weather(location: str):
    """A mock local function that our tool will execute."""
    print(f"\n[LOCAL EXECUTION] ☁️ Fetching weather for {location}...")
    # In a real app, this would be an API call to a weather service
    return {"temperature": "72°F", "condition": "Sunny", "location": location}

# =====================================================================
# Stop Reasons Demonstration
# =====================================================================
def run_stop_reasons_example():
    print("=" * 80)
    print("🚦 RUNNING STOP REASONS LIFECYCLE EXAMPLE")
    print("=" * 80)

    # 1. Initial Prompt
    messages = [{"role": "user", "content": "What is the weather in Tokyo?"}]
    print("User: What is the weather in Tokyo?\n")

    # 2. First API Call
    print(">>> 1. Sending first API call to Claude (giving it the tool)...")
    response_1 = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1024,
        tools=[get_weather_tool],
        messages=messages
    )

    # 3. Check the First Stop Reason
    print(f"    ✅ Response 1 Stop Reason: '{response_1.stop_reason}'")
    
    if response_1.stop_reason == "tool_use":
        print("    (Notice: Claude paused generation because it wants to use a tool!)\n")
        
        # We must append Claude's response (which contains the tool_use block) to our history
        messages.append({"role": "assistant", "content": response_1.content})
        
        # Find the tool_use block
        tool_use_block = next(block for block in response_1.content if block.type == "tool_use")
        print(f"    Claude requested tool: {tool_use_block.name} with args: {tool_use_block.input}")
        
        # 4. Execute the tool locally
        location = tool_use_block.input["location"]
        weather_data = mock_get_weather(location)
        
        # 5. Provide the Tool Result back to Claude
        print("\n>>> 2. Appending the tool_result and making the second API call...")
        tool_result_message = {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": json.dumps(weather_data)
                }
            ]
        }
        messages.append(tool_result_message)

        # 6. Second API Call
        response_2 = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1024,
            tools=[get_weather_tool],
            messages=messages
        )

        # 7. Check the Final Stop Reason
        print(f"    ✅ Response 2 Stop Reason: '{response_2.stop_reason}'")
        if response_2.stop_reason == "end_turn":
            print("    (Notice: Claude has naturally finished its response!)\n")
        
        # Print final text
        final_text = next(block.text for block in response_2.content if block.type == "text")
        print(f"Claude's Final Output: {final_text}")

if __name__ == "__main__":
    run_stop_reasons_example()
