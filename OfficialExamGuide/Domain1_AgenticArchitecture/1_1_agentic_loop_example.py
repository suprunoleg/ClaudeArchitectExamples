"""
Task Statement 1.1: Design and implement agentic loops for autonomous task execution

Knowledge of:
- The agentic loop lifecycle: sending requests to Claude, inspecting stop_reason ("tool_use" vs "end_turn"), executing requested tools, and returning results for the next iteration
- How tool results are appended to conversation history so the model can reason about the next action
- The distinction between model-driven decision-making and pre-configured decision trees

Skills in:
- Implementing agentic loop control flow that continues when stop_reason is "tool_use" and terminates when stop_reason is "end_turn"
- Adding tool results to conversation context between iterations
- Avoiding anti-patterns (parsing natural language signals to determine loop termination, arbitrary iteration caps)
"""

import os
import pprint
from anthropic import Anthropic

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

# Initialize native Anthropic client for direct API access
client = Anthropic()

def get_server_status(region: str) -> str:
    """A simple tool implementation."""
    return f"The server in {region} is currently ONLINE and operating at 42% capacity."

# EXAM SKILL: Model-driven decision-making. 
# We define tools, but Claude decides IF and WHEN to use them based on context.
TOOLS = [
    {
        "name": "get_server_status",
        "description": "Get the current operational status and capacity of a regional server.",
        "input_schema": {
            "type": "object",
            "properties": {
                "region": {"type": "string", "description": "The server region (e.g., us-east-1)"}
            },
            "required": ["region"]
        }
    }
]

def run_agentic_loop(prompt: str):
    # Initialize the conversation history
    messages = [{"role": "user", "content": prompt}]
    
    # EXAM SKILL: Agentic loop control flow.
    # The loop runs indefinitely until a specific stop_reason is encountered.
    # We avoid the anti-pattern of using an arbitrary iteration cap (e.g., `for i in range(5)`) as the primary stopping mechanism.
    while True:
        try:
            # 1. Send request to Claude with tools and accumulated history
            response = client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=1024,
                tools=TOOLS,
                messages=messages
            )
            
            # 2. Append Claude's response (text or tool_use blocks) to history
            messages.append({"role": "assistant", "content": response.content})
            
            # 3. Inspect stop_reason
            # EXAM SKILL: Terminating strictly when stop_reason is "end_turn".
            # We avoid the anti-pattern of parsing natural language (e.g., checking if text contains "I am done").
            if response.stop_reason == "end_turn":
                break
                
            # EXAM SKILL: Continuing loop when stop_reason is "tool_use".
            elif response.stop_reason == "tool_use":
                
                # 4. Execute requested tools and gather results
                tool_results = []
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        
                        if tool_name == "get_server_status":
                            # Execute the tool
                            result = get_server_status(tool_input["region"])
                            
                            # EXAM SKILL: Formatting tool results properly
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": result
                            })
                
                # EXAM SKILL: Appending tool results to conversation context for the next iteration
                messages.append({"role": "user", "content": tool_results})
            
            # Handle other stop reasons gracefully (e.g., max_tokens)
            else:
                break
                
        except Exception:
            # Handle API errors (expected when using dummy_key)
            break
            
    print("\n=== FINAL CONVERSATION STATE ===")
    pprint.pprint(messages, indent=2)

if __name__ == "__main__":
    run_agentic_loop("Can you check the status of the us-east-1 server and tell me if it's healthy?")
