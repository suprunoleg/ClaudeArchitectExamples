"""
Task Statement 2.1: Design effective tool interfaces with clear descriptions and boundaries
(API VERSION)

Knowledge of:
- How the LLM interprets tool descriptions and parameter descriptions as part of its system prompt.
- The impact of poorly bounded tools (e.g., overlapping functionality) on routing reliability.

Skills in:
- Writing unambiguous tool descriptions that specify exactly what the tool does, what it returns, and when NOT to use it.
- Enforcing strict typing, enums, and required parameters in JSON schema.
"""

import os
import asyncio
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = AsyncAnthropic()

# ==============================================================================
# ==============================================================================

BAD_TOOL_SCHEMA = {
    "name": "get_data",
    "description": "Gets data about users or orders.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query_type": {"type": "string"},
            "id": {"type": "string"}
        },
        # Missing required array entirely! Model might omit 'id'.
    }
}

GOOD_TOOL_SCHEMA = {
    "name": "get_user_profile",
    "description": (
        "Retrieves the complete profile for a single verified user. "
        "Returns the user's name, email, and account tier. "
        "DO NOT use this tool to search for users by name; you must have the exact User ID."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The exact alphanumeric User ID (e.g., 'U-12345')."
            },
            "detail_level": {
                "type": "string",
                "description": "How much data to return. Must be 'basic' or 'full'.",
                "enum": ["basic", "full"] # Forces the model to pick a valid option
            }
        },
        "required": ["user_id", "detail_level"] # Ensures model provides both
    }
}


# ==============================================================================
# WORKFLOW
# ==============================================================================

def run_get_user_profile(user_id: str, detail_level: str) -> str:
    """Mock execution of the tool."""
    return f"User {user_id} profile ({detail_level}): Alice, alice@example.com, Tier: Premium"

async def run_tool_design_api(user_request: str):
    
    messages = [{"role": "user", "content": user_request}]
    
    # ANTI-TOKEN-HOG RULE: Limit iterations
    max_iterations = 2
    
    for i in range(max_iterations):
        try:
            # We supply only the GOOD tool schema
            response = await client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=1000,
                messages=messages,
                tools=[GOOD_TOOL_SCHEMA]
            )
        except Exception as e:
            return "Workflow failed."
            
        messages.append({"role": "assistant", "content": response.content})
        
        if response.stop_reason == "tool_use":
            for block in response.content:
                if block.type == "tool_use":
                    
                    if block.name == "get_user_profile":
                        res = run_get_user_profile(**block.input)
                    else:
                        res = f"Unknown tool {block.name}"
                        
                    messages.append({
                        "role": "user",
                        "content": [{"type": "tool_result", "tool_use_id": block.id, "content": res}]
                    })
        else:
            return next((b.text for b in response.content if b.type == 'text'), "")

    return "Max iterations reached."

if __name__ == "__main__":
    req = "Can you look up the full profile for user U-999?"
    res = asyncio.run(run_tool_design_api(req))
